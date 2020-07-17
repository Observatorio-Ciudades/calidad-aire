################################################################################
# Module: utils.py
# Set of utility functions 
# developed by: Luis Natera @natera
# 			  nateraluis@gmail.com
# updated: 02/01/20
################################################################################

import pandas as pd
import geopandas as gpd
import osmnx as ox
import os
import igraph as ig
import numpy as np
from h3 import h3
import shapely
import logging
import datetime as dt
from shapely.geometry import Point, Polygon
from matplotlib.patches import RegularPolygon


def find_nearest(G, gdf, amenity_name):
	"""
	Find the nearest graph nodes to the points in a GeoDataFrame

	Arguments:
		G {networkx.Graph} -- Graph created with OSMnx that contains geographic information (Lat,Lon, etc.)
		gdf {geopandas.GeoDataFrame} -- GeoDataFrame with the points to locate
		amenity_name {str} -- string with the name of the amenity that is used as seed (pharmacy, hospital, shop, etc.)

	Returns:
		geopandas.GeoDataFrame -- GeoDataFrame original dataframe with a new column call 'nearest' with the node id closser to the point
	"""
	gdf['x'] = gdf['geometry'].apply(lambda p: p.x)
	gdf['y'] = gdf['geometry'].apply(lambda p: p.y)
	gdf[f'nearest_{amenity_name}'] = ox.get_nearest_nodes(G,list(gdf['x']),list(gdf['y']))
	return gdf

def to_igraph(G):
	"""
	Convert a graph from networkx to igraph

	Arguments:
		G {networkx.Graph} -- networkx Graph to be converted

	Returns:
		igraph.Graph -- Graph with the same number of nodes and edges as the original one
		np.array  -- With the weight of the graph, if the original graph G is from OSMnx the weights are lengths
		dict -- With the node mapping, index is the node in networkx.Graph, value is the node in igraph.Graph
	"""
	node_mapping = dict(zip(G.nodes(),range(G.number_of_nodes())))
	g = ig.Graph(len(G), [(node_mapping[i[0]],node_mapping[i[1]]) for i in G.edges()])
	weights=np.array([float(e[2]['length']) for e in G.edges(data=True)])
	node_id_array=np.array(list(G.nodes())) #the inverse of the node_mapping (the index is the key)
	assert g.vcount() == G.number_of_nodes()
	return g, weights, node_mapping

def get_seeds(gdf, node_mapping, amenity_name):
	"""
	Generate the seed to be used to calculate shortest paths for the Voronoi's

	Arguments:
		gdf {geopandas.GeoDataFrame} -- GeoDataFrame with 'nearest' column
		node_mapping {dict} -- dictionary containing the node mapping from networkx.Graph to igraph.Graph

	Returns:
		np.array -- numpy.array with the set of seeds
	"""
	# Get the seed to calculate shortest paths
	return np.array(list(set([node_mapping[i] for i in gdf[f'nearest_{amenity_name}']])))

def haversine(coord1, coord2):
	"""
	Calculate distance between two coordinates in meters with the Haversine formula

	Arguments:
		coord1 {tuple} -- tuple with coordinates in decimal degrees (e.g. 43.60, -79.49)
		coord2 {tuple} -- tuple with coordinates in decimal degrees (e.g. 43.60, -79.49)

	Returns:
		float -- distance between coord1 and coord2 in meters
	"""
	# Coordinates in decimal degrees (e.g. 43.60, -79.49)
	lon1, lat1 = coord1
	lon2, lat2 = coord2
	R = 6371000  # radius of Earth in meters
	phi_1 = np.radians(lat1)
	phi_2 = np.radians(lat2)    
	delta_phi = np.radians(lat2 - lat1)
	delta_lambda = np.radians(lon2 - lon1)    
	a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi_1) * np.cos(phi_2) * np.sin(delta_lambda / 2.0) ** 2    
	c = 2 * np.arctan2(np.sqrt(a),np.sqrt(1 - a))    
	meters = R * c  # output distance in meters
	km = meters / 1000.0  # output distance in kilometers    
	return meters

def create_hexgrid(polygon, hex_res, geometry_col='geometry',buffer=0.000):
	"""
	Takes in a geopandas geodataframe, the desired resolution, the specified geometry column and some map parameters to create a hexagon grid (and potentially plot the hexgrid

	Arguments:
		polygon {geopandas.geoDataFrame} -- geoDataFrame to be used
		hex_res {int} -- Resolution to use

	Keyword Arguments:
		geometry_col {str} -- column in the geoDataFrame that contains the geometry (default: {'geometry'})
		buffer {float} -- buffer to be used (default: {0.000})

	Returns:
		geopandas.geoDataFrame -- geoDataFrame with the hexbins and the hex_id_{resolution} column
	"""
	centroid = list(polygon.centroid.values[0].coords)[0]

	# Explode multipolygon into individual polygons
	exploded = polygon.explode().reset_index(drop=True)

	# Master lists for geodataframe
	hexagon_polygon_list = []
	hexagon_geohash_list = []

	# For each exploded polygon
	for poly in exploded[geometry_col].values:

		# Reverse coords for original polygon
		reversed_coords = [[i[1], i[0]] for i in list(poly.exterior.coords)]

		# Reverse coords for buffered polygon
		buffer_poly = poly.buffer(buffer)
		reversed_buffer_coords = [[i[1], i[0]] for i in list(buffer_poly.exterior.coords)]

		# Format input to the way H3 expects it
		aoi_input = {'type': 'Polygon', 'coordinates': [reversed_buffer_coords]}

		# Generate list geohashes filling the AOI
		geohashes = list(h3.polyfill(aoi_input, hex_res))
		for geohash in geohashes:
			polygons = h3.h3_set_to_multi_polygon([geohash], geo_json=True)
			outlines = [loop for polygon in polygons for loop in polygon]
			polyline_geojson = [outline + [outline[0]] for outline in outlines][0]
			hexagon_polygon_list.append(shapely.geometry.Polygon(polyline_geojson))
			hexagon_geohash_list.append(geohash)

	# Create a geodataframe containing the hexagon geometries and hashes
	hexgrid_gdf = gpd.GeoDataFrame()
	hexgrid_gdf['geometry'] = hexagon_polygon_list
	id_col_name = 'hex_id_' + str(hex_res)
	hexgrid_gdf[id_col_name] = hexagon_geohash_list
	hexgrid_gdf.crs = {'init' :'epsg:4326'}

	# Drop duplicate geometries
	geoms_wkb = hexgrid_gdf["geometry"].apply(lambda geom: geom.wkb)
	hexgrid_gdf = hexgrid_gdf.loc[geoms_wkb.drop_duplicates().index]

	return hexgrid_gdf


################################################################################
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 17/07/20
################################################################################

def pollutant(p):
    """Function that returns a str with a pollutant chemical form

    Args:
        p {int} -- values from 0 to 5 for list place

    Returns:
        str -- str with pollutant chemical form
    """
    #criterion pollutant chemical formula
    param = ['CO','NO2', 'O3','PM10','SO2']

    return (param[p])

def city_valid_aqip(pollutant, tresh=0.75):
    """Function that aquieres list of cities that have equal or greater data coverage according to treshold value

    Args:
        pollutant {str} -- pollutant coverage to be analyzed
        tresh {float} -- treshold limit to be analyzed, set default to 0.75

    Returns:
        list -- list with city names
    """
    #Open csv with statistics of data coverage from AQIP for mexican cities
    stat_mx = pd.read_csv('../data/processed/aqip/MX_StatRes_2017-2020.csv', encoding='latin_1').set_index('City')

    #Filters dataframe according to pollutant
    stat_mx = stat_mx[stat_mx['Specie']==pollutant]

    #Filters dataframe according to treshold
    stat_mx = stat_mx[stat_mx['Pctg']>=tresh]
    
    city_list = stat_mx.index.tolist()
    
    return (city_list)

def catch_outliers(pollutant):
    """Function that returns limit value for pollutant outliers based on: https://rama.edomex.gob.mx/imeca

    Args:
        pollutant {str} -- pollutant for limit

    Returns:
        int - limit value above which is considered outlier
    """
    #List with limit values
    outlier = {'PM10':464, 'O3':454, 'CO':22,
               'PM25':300, 'SO2':195,'NO2':420}
    
    return (outlier[pollutant])

def city_name(city):
    """Function that returns city name based city code

    Args:
        city {str} -- city code

    Returns:
        str -- city name
    """
    #Dictionary with city code and name
    city_dict = {'cdmx':'Valle de México',
                'gdl':'Guadalajara',
                'mty':'Monterrey'}
    
    return (city_dict[city])

def o3_conc(x):
    """Function that calculates the concentration of a pollutant based on air quality index based on 
        equations from: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

    Args:
        x {int} -- air quality index of the pollutant

    Returns:
        float -- concentration of the pollutant
    """
    conc = 0
    if x <= 50:
        conc = ((x-0)*(0.054-0))/(50-0)+0
    elif x>50 and x<=100:
        conc = ((x-51)*(0.070-0.055))/(100-51)+0.055
    elif x>100 and x<=150:
        conc = ((x-101)*(0.085-0.071))/(150-101)+0.071
    elif x>150 and x<=200:
        conc = ((x-151)*(0.105-0.086))/(200-151)+0.086
    elif x>200 and x<=300:
        conc = ((x-201)*(0.200-0.106))/(300-201)+0.106
        
    return (conc*1000) #multiplies by 1000 to convert from ppm to ppb

def co_conc(x):
    """Function that calculates the concentration of a pollutant based on air quality index based on 
        equations from: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

    Args:
        x {int} -- air quality index of the pollutant

    Returns:
        float -- concentration of the pollutant
    """

    conc = 0
    if x <= 50:
        conc = ((x-0)*(4.4-0))/(50-0)+0
    elif x>50 and x<=100:
        conc = ((x-51)*(9.4-4.5))/(100-51)+4.5
    elif x>100 and x<=150:
        conc = ((x-101)*(12.4-9.5))/(150-101)+9.5
    elif x>150 and x<=200:
        conc = ((x-151)*(15.4-12.5))/(200-151)+12.5
    elif x>200 and x<=300:
        conc = ((x-201)*(30.4-15.5))/(300-201)+15.5
    elif x>300 and x<=400:
        conc = ((x-301)*(40.4-30.5))/(400-301)+30.5
    elif x>400:
        conc = ((x-401)*(50.4-40.5))/(500-401)+40.5
        
    return (conc)

def pm10_conc(x):
    """Function that calculates the concentration of a pollutant based on air quality index based on 
        equations from: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

    Args:
        x {int} -- air quality index of the pollutant

    Returns:
        float -- concentration of the pollutant
    """

    conc = 0
    if x <= 50:
        conc = ((x-0)*(54-0))/(50-0)+0
    elif x>50 and x<=100:
        conc = ((x-51)*(154-55))/(100-51)+55
    elif x>100 and x<=150:
        conc = ((x-101)*(254-155))/(150-101)+155
    elif x>150 and x<=200:
        conc = ((x-151)*(354-255))/(200-151)+255
    elif x>200 and x<=300:
        conc = ((x-201)*(424-355))/(300-201)+355
    elif x>300 and x<=400:
        conc = ((x-301)*(504-425))/(400-301)+425
    elif x>400:
        conc = ((x-401)*(604-505))/(500-401)+505
        
    return (conc)
        
def pm25_conc(x):
    """Function that calculates the concentration of a pollutant based on air quality index based on 
        equations from: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

    Args:
        x {int} -- air quality index of the pollutant

    Returns:
        float -- concentration of the pollutant
    """

    conc = 0
    if x <= 50:
        conc = ((x-0)*(12-0))/(50-0)+0
    elif x>50 and x<=100:
        conc = ((x-51)*(35.4-12.1))/(100-51)+12.1
    elif x>100 and x<=150:
        conc = ((x-101)*(55.4-35.5))/(150-101)+35.5
    elif x>150 and x<=200:
        conc = ((x-151)*(150.4-55.5))/(200-151)+55.5
    elif x>200 and x<=300:
        conc = ((x-201)*(250.4-150.5))/(300-201)+150.5
    elif x>300 and x<=400:
        conc = ((x-301)*(350.4-250.5))/(400-301)+250.5
    elif x>400:
        conc = ((x-401)*(500.4-350.5))/(500-401)+350.5
        
    return (conc*1.0)

def so2_conc(x):
    """Function that calculates the concentration of a pollutant based on air quality index based on 
        equations from: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

    Args:
        x {int} -- air quality index of the pollutant

    Returns:
        float -- concentration of the pollutant
    """

    conc = 0
    if x <= 50:
        conc = ((x-0)*(35-0))/(50-0)+0
    elif x>50 and x<=100:
        conc = ((x-51)*(75-36))/(100-51)+36
    elif x>100 and x<=150:
        conc = ((x-101)*(185-76))/(150-101)+76
    elif x>150 and x<=200:
        conc = ((x-151)*(304-186))/(200-151)+186
    elif x>200 and x<=300:
        conc = ((x-201)*(604-305))/(300-201)+305
    elif x>300 and x<=400:
        conc = ((x-301)*(804-605))/(400-301)+605
    elif x>400:
        conc = ((x-401)*(1004-805))/(500-401)+805 
        
    return (conc)

def no2_conc(x):
    """Function that calculates the concentration of a pollutant based on air quality index based on 
        equations from: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

    Args:
        x {int} -- air quality index of the pollutant

    Returns:
        float -- concentration of the pollutant
    """

    conc = 0
    if x <= 50:
        conc = ((x-0)*(53-0))/(50-0)+0
    elif x>50 and x<=100:
        conc = ((x-51)*(100-54))/(100-51)+54
    elif x>100 and x<=150:
        conc = ((x-101)*(360-101))/(150-101)+101
    elif x>150 and x<=200:
        conc = ((x-151)*(649-361))/(200-151)+361
    elif x>200 and x<=300:
        conc = ((x-201)*(1249-650))/(300-201)+650
    elif x>300 and x<=400:
        conc = ((x-301)*(1649-1250))/(400-301)+1250
    elif x>400:
        conc = ((x-401)*(2049-1650))/(500-401)+1650
        
    return (conc*1.0)


def p_limits(pollutant):
	"""Function that returns a limit value for a bad air quality

	Args:
		pollutant {str} -- chemical foruma of pollutant

	Returns:
		int -- int with limit value
	"""
	
	limit_dict = {'PM10':150, 'O3':100, 'CO':16.5, 'PM25':97.4, 'SO2':100,'NO2':315}
	
	return (limit_dict[pollutant])

def p_unit (pollutant):
	"""Function that returns the measure unit depending on the pollutant

	Args:
		pollutant {str} -- chemical foruma of pollutant

	Returns:
		str -- str with measure unit
	"""

	unit_dict = {'PM10':'(ppm)', 'O3':'(ppb)', 'CO':'(ppb)','PM25':'(ppb)', 'SO2':'(ppb)','NO2':'(ppb)'}
	
	return (unit_dict[pollutant])