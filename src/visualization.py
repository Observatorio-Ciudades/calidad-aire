################################################################################
# Module: Station visualizer
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 17/07/2020
################################################################################

import folium
from datosgobmx import client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from math import sqrt
import geopandas as gpd
import src
import os
import sys
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely.geometry import Point
from math import sqrt
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)



plt.style.use('https://github.com/dhaitz/matplotlib-stylesheets/raw/master/pitayasmoothie-dark.mplstyle')

def compare_aq(p, city, multiplier=1.0):
    """Function that creates a scatter plot from AQIP data base for a given city and that city's air quality stations
        for a given pollutant

    Args:
        p {str} -- str with chemical formula for analyzed pollutant
        city {str} -- str with code for the city analyzed
        multiplier {float} -- specifies if the AQIP data was displaced by multiplier, set to 1.0 by default

    Returns:
        plot -- scatter plot with the data from AQIP and air quality stations
    """


    dir_pcs = '../data/processed/'
    dir_pcs_cat = dir_pcs+'aqip_'+city #Directory with merged data
    dir_fig_cmp = '../output/figures/aqip_analysis/' #Directory to save plot

    compare = pd.read_csv(dir_pcs_cat +city+'_AQIP.csv')
    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                                'Date':'Fecha'})
    ax = plt.gca()
    compare[compare['Contaminante']==p].plot(kind='scatter', x='Fecha',y='cdmx_median', ax=ax)
    compare[compare['Contaminante']==p].plot(kind='scatter', x='Fecha',y='aqip_median', alpha = 0.75, ax=ax)
    
    plt.ylabel('Concentration: '+p)
    
    plt.savefig(dir_fig_cmp+p+'_x'+str(multiplier)+'.png', dpi=100)
    
    #plt.show()

def visualize_stations():
    """Function that creates folium map to visualize air quality stations in Mexico based on the SINAICA database,
        code based on: https://datos.gob.mx/blog/ventilando-datos-abiertos-sobre-calidad-del-aire

    Returns:
        folium_map -- folium_map with information from all mexican air quality stations
    """

    #calls datosgobmx and gets json with data from stations
    parametros_request = client.makeCall('sinaica-estaciones',{'pageSize':200})

    stations = []

    for v in parametros_request['results']:
        aux = pd.DataFrame.from_dict(v,orient='index').T
        stations.append(aux)

    stations = pd.concat(stations, ignore_index=True)
    
    #Removes stations outside of Mexico
    mask = (stations.lat.between(14, 34.5)) & (stations.long.between(-120, -70))
    stations = stations[mask]

    centro_lat, centro_lon = 22.396092, -101.731430 #Center of the folium_map

    #Creates map
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=5,
                            tiles = 'cartodb positron')

    #Adds stations points
    for row in stations.iterrows():

        #Puntos con nombre, latitud y longitud
        popup_text = f"<b> Nombre: </b> {row.nombre} <br> <b> Latitud: </b> {row.lat:.5f} <br> <b> Longitud: </b> {row.long:.5f} <br>"

        #Coloca los marcadores en el mapa
        folium.CircleMarker(location=[row.lat, row.long], radius=5,
                            tooltip = popup_text, fill=True, fill_opacity=0.4).add_to(folium_map)

    return folium_map


def imeca_colors (param, conc):
    """Function that takes a pollutant and concentration, calculates its IMECA and returns a hex,
        IMECA calculation based on: https://rama.edomex.gob.mx/imeca

    Args:
        param {str} -- str with criteron pollutant chemical formula
        conc {float} -- concentration for the pollutant

    Returns:
        str -- sr with the hex code
    """
    
    imeca = 0
    
    if param == 'CO':
    
        imeca = conc * 100 / 11
        
    elif param == 'SO2':
    
        imeca = (conc/1000) * 100 / 0.11
        
    elif param == 'NO2':
    
        imeca = (conc/1000) * 100 / 0.21
        
    elif param == 'O3':
        
        conc = conc/1000
        
        if conc <= 0.07:
            imeca = 714.29*conc
        
        elif 0.07 < conc <= 0.095:
            imeca = 2041.67*(conc-0.071)+51
            
        elif 0.095 < conc <= 0.154:
            imeca = 844.83*(conc-0.096)+101
            
        elif 0.154 < conc <= 0.204:
            imeca = 1000*(conc-0.155)+151
            
        elif 0.204 < conc <= 0.404:
            imeca = 497.49*(conc-0.205)+201
        
        elif 0.404 < conc:
            imeca = 1000*(conc-104)
            
    elif param == 'PM10':
        
        if conc <= 40:
            imeca = 1.25*conc
        
        elif 40 < conc <= 75:
            imeca = 1.44*(conc-41)+51
            
        elif 75 < conc <= 214:
            imeca = 0.355*(conc-76)+101
            
        elif 214 < conc <= 354:
            imeca = 0.353*(conc-215)+151
            
        elif 354 < conc <= 424:
            imeca = 1.4359*(conc-355)+201
        
        elif 424 < conc <= 504:
            imeca = 1.253*(conc-425)+301
            
        elif 504 < conc:
            imeca = conc-104
            
    if imeca <= 50:
        color = '#75b46f'
        
    elif 50 < imeca <= 100:
        color = '#f7ff55'
        
    elif 100 < imeca <= 150:
        color = '#ff9e4f'
        
    elif 150  < imeca <= 200:
        color = '#db3331'
    
    elif 200 < imeca:
        color = '#c158b8'
        
    else:
        color = '#ffffff'
        
    return (color)

def visualize_aqdata_date(city, pollutant, date, year_limit=2020, zoom=10):
    """ Creates a folium map with stations arranged by size and colour depending on the concentration of the pollutant

    Args:
        city {str} -- code for the city to be analysed, for example: cdmx
        pollutant {str} -- chemical formula of pollutant to be plotted
        date {str} -- date to be analysed in format yyyy-mm-dd
        year_limit{int} -- int with the limit year for the city's database, set to 2020 by default
        zoom{int} -- zoom start value for the folium_map, set to 10 by default

    Returns:
        folium map
    """
    dir_pcs = '../data/processed/'

    city_stations = pd.read_csv('../data/raw/Grl/stations/city_stations.csv') #csv with stations by city

    data_csv = dir_pcs+city+'/'+city+'_2017-'+str(year_limit)+'_'+pollutant+'.csv'
    
    data_bydateParam = pd.read_csv(data_csv).set_index('FECHA')
    
    #lists to append valid values of lat and long to set the center
    
    x = []
    y = []
    
    for i,est in city_stations[city_stations['city']==src.city_name(city)].iterrows():

                est_code = city_stations.loc[(i),'codigo']
                c_value = data_bydateParam.loc[(date),est_code]
                
                #saves coordinates of stations with data
                if pd.notna(c_value):
                    x.append(est.long)
                    y.append(est.lat)

    #Registers the boundries coordinates to set a center
    min_x = min(x)
    max_x = max(x)
    min_y = min(y)
    max_y = max(y)
    
    centro_lon = (min_x+max_x)/2
    centro_lat = (min_y+max_y)/2

    #Creacion del mapa
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=zoom,
                            tiles = 'cartodb positron')

    for i, est in city_stations[city_stations['city']==src.city_name(city)].iterrows():

        est_code = city_stations.loc[(i),'codigo']

        #Coloca los marcadores en el mapa
        c_value = data_bydateParam.loc[(date),est_code]
        c_graph = (data_bydateParam.loc[(date),est_code])/src.p_limits(pollutant)

        #Puntos con nombre, latitud y longitud
        popup_text = f"<b> Nombre: </b> {est.nombre} <br> <b> Latitud: </b> {est.lat:.5f} <br> <b> Longitud: </b> {est.long:.5f} <br> <b> Contaminante: </b> {pollutant} <br> <b> Conc: </b> {c_value} <br>"

        #Coloca los marcadores en el mapa
        folium.CircleMarker(location=[est.lat, est.long], radius=c_graph*50,
                            tooltip = popup_text, fill=True, color=imeca_colors(pollutant, c_graph),
                            fill_opacity=0.65).add_to(folium_map)

    return(folium_map)

def clr_change(conc_cmp):
    """Function that receives a float of a normalyzed concentration and returns a hex

    Args:
        conc_cmp {float} -- value resulted from the division bewteen the concentration of the year analysed and the year prior

    Returns:
        str -- str with the hex code, if the value of the current year is smaller it's blue, otherwise it's red.
    """
    
    if conc_cmp>=0:
        color = '#F84A50'
    else:
        color = '#6086CA'
        
    return color

def compare_year_prior(city, pollutant, date, year_limit=2020, zoom=10):
    """Creates a map with the analysis of the average between the week previous to the input date 
        and the weeek of the previous year for a selected pollutant

    Args:
        city {str} -- code for the city to be analyzed, for example: cdmx
        pollutant {str} -- pollutant to be plotted
        date {str} -- date to be analyzed in format yyyy-mm-dd
        year_limit{int} -- int with the limit year for the city's database, set to 2020 by default
        zoom{int} -- zoom start value for the folium_map

    Returns:
        folium_map -- folium map where a blue marker indicates a smaller value of the input date concentration and, 
                        the bigger the marker the larger the concentration
    """
    city_stations = pd.read_csv('../data/raw/Grl/stations/city_stations.csv') #csv with stations by city

    dir_pcs = '../data/processed/'
    
    prev_year = str(int(date[:4])-1)+date[4:]
    
    data_csv = dir_pcs+city+'/'+city+'_2017-'+str(year_limit)+'_'+pollutant+'.csv'
    
    data_bydateParam = pd.read_csv(data_csv).set_index('FECHA')
    
    #lists to append valid values of lat and long to set the center
    
    x = []
    y = []
    
    for i, est in city_stations[city_stations['city']==src.city_name(city)].iterrows():

                est_code = city_stations.loc[(i),'codigo']
                c_value = data_bydateParam.loc[(date),est_code]
                
                #saves coordinates of stations with data
                if pd.notna(c_value):
                    x.append(est.long)
                    y.append(est.lat)

   #Registers the boundries coordinates to set a center
    min_x = min(x)
    max_x = max(x)
    min_y = min(y)
    max_y = max(y)
    
    cnt_x = (min_x+max_x)/2
    cnt_y = (min_y+max_y)/2
    
    
    centro_lat, centro_lon = cnt_y, cnt_x #Centro del mapa

    #Creacion del mapa
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=zoom,
                            tiles = 'cartodb positron')

    for i, est in city_stations[city_stations['city']==src.city_name(city)].iterrows():

        est_code = city_stations.loc[(i),'codigo']

        #Coloca los marcadores en el mapa
        c_current = data_bydateParam.loc[(date),est_code]
        c_prev = data_bydateParam.loc[(prev_year),est_code]
        c_graph = (c_current - c_prev)/c_prev

        #Puntos con nombre, latitud y longitud
        popup_text = f"<b> Nombre: </b> {est.nombre} <br> <b> Latitud: </b> {est.lat:.5f} <br> <b> Longitud: </b> {est.long:.5f} <br> <b> Contaminante: </b> {pollutant} <br> <b> Conc: </b> {c_graph} <br>"

        #Coloca los marcadores en el mapa
        folium.CircleMarker(location=[est.lat, est.long], radius=abs(c_graph)*50,
                            tooltip = popup_text, fill=True, color=clr_change(c_graph),
                            fill_opacity=0.65).add_to(folium_map)

    return(folium_map)

def interpolate_aqdata_date(city, pollutant, date, year_limit=2020, cellsize=0.01):
    """Function that creates a folium map with user specified city, pollutant and date and interpolates valid values


        Args:
            city {str} -- code for the city to be analyzed, for example: cdmx
            pollutant {str} -- pollutant to be plotted
            date {str} -- date to be analyzed in format yyyy-mm-dd
            year_limit{int} -- int with the limit year for the city's database, set to 2020 by default
            cell_size{float} -- cell size for the interpolation in degrees, set to 0.01 by default

        Returns:
            folium_map -- folium map with interpolated data for the specified date and pollutant
    """

    dir_pcs = '../data/processed/'

    city_stations = pd.read_csv('../data/raw/Grl/stations/city_stations.csv') #csv with stations by city


    data_csv = dir_pcs+city+'/'+city+'_2017-'+str(year_limit)+'_'+pollutant+'.csv'
    
    data_bydateParam = pd.read_csv(data_csv).set_index('FECHA')
    
    #lists to append valid values of lat and long for interpolation
    
    x = []
    y = []
    
    for i, est in city_stations[city_stations['city']==src.city_name(city)].iterrows():

                est_code = city_stations.loc[(i),'codigo']
                c_value = data_bydateParam.loc[(date),est_code]
                
                #saves coordinates of stations with air quality data
                if pd.notna(c_value):
                    x.append(est.long)
                    y.append(est.lat)

    #Registers the boundries coordinates for the interpolation
    min_x = min(x)
    max_x = max(x)
    min_y = min(y)
    max_y = max(y)

    folium_map = visualize_aqdata_date(city, pollutant, date)

    #Valor de celda
    cellsize = 0.01
    #Valor de potencia
    p = 2

    #x and y values for the start of the interpolation
    xidw=min_x
    yidw=min_y

    #Variables for interpolation
    dividendo = 0
    divisor = 0
    idw=[]

    while xidw <= max_x:
        while yidw <= max_y:
            for i, est in city_stations[city_stations['city']==src.city_name(city)].iterrows():

                est_code = city_stations.loc[(i),'codigo']
                c_value = data_bydateParam.loc[(date),est_code]

                if pd.notna(c_value):
                    dividendo = (c_value/(sqrt((est.long-xidw)**2+(est.lat-yidw)**2)**(p)))+ dividendo
                    divisor = (1/(sqrt((est.long-xidw)**2+(est.lat-yidw)**2)**(p))) + divisor

            concentracion = dividendo/divisor
            #Aqui se guardan los valores de las concentraciones para usarlos despues

            c_graph = concentracion/src.p_limits(pollutant)

            #Puntos con nombre, latitud y longitud
            popup_text = f"<b> Nombre: </b> {'NA'} <br> <b> Latitud: </b> {yidw:.5f} <br> <b> Longitud: </b> {xidw:.5f} <br> <b> Contaminante: </b> {pollutant} <br> <b> Conc: </b> {concentracion} <br>"

            #Coloca los marcadores en el mapa
            folium.CircleMarker(location=[yidw, xidw], radius=1,
                                tooltip = popup_text, fill=True, color=imeca_colors(pollutant, c_graph),
                                opacity=0.45).add_to(folium_map)

            idw.append([yidw,xidw,concentracion])
            yidw = yidw + cellsize
            dividendo = 0
            divisor = 0  
        xidw = xidw + cellsize
        yidw = min_y


    return(folium_map)

def visualize_mx_aqip(pollutant, date, year_limit=2020, zoom=5):
    """Function that returns a folium map with the air quality by city for a given date according to AQIP

    Args:
        pollutant {str} -- str with the chemical formula for teh criterion pollutant
        date {str} -- date to be analyzed in format yyyy-mm-dd
        year_limit{int} -- int with the limit year for the city's database, set to 2020 by default
        zoom{int} -- zoom start value for the folium_map

    Returns:
        folium_map -- folium_map of Mexico with city centroids colored according to pollutant level
    """
    
    
    dir_ext = '../data/external/INEGI/'
    
    dir_pcs = '../data/processed/'
    
    mx_mun = pd.read_csv(dir_ext+'CentroidMunicipalities_INEGI19_v1.csv', encoding ='latin_1')
    
    aqip_mx = pd.read_csv(dir_pcs+'aqip/MX_'+pollutant+'_2017-'+str(year_limit)+'.csv', encoding='latin_1').set_index('Date')
    
    
    centro_lat, centro_lon = 22.396092, -101.731430 #Centro del mapa

    #Creacion del mapa
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=zoom,
                            tiles = 'cartodb positron')
    
    cty_aqip = [c for c in aqip_mx.columns] #gets all cities in database into list
    
    for i in range(1,len(cty_aqip)):
        
        city = cty_aqip[i]
        
        #specify names for Oaxaca and Mexico city
        if city == 'Oaxaca':
            city = 'Oaxaca de Juárez'
        
        elif city == 'Mexico City':
            city = 'Ciudad de México'
        
        c_value = aqip_mx.loc[date,cty_aqip[i]]
        
        lat = float(mx_mun[mx_mun['NOMGEO']==city].lat)
        
        long = float(mx_mun[mx_mun['NOMGEO']==city].long)
 
        #City centroids with name, latitude, longitude, pollutant and concentration
        popup_text = f"<b> Nombre: </b> {city} <br> <b> Latitud: </b> {lat:.5f} <br> <b> Longitud: </b> {long:.5f} <br> <b> Contaminante: </b> {pollutant} <br> <b> Conc: </b> {c_value} <br>"

        #adds points to map
        folium.CircleMarker(location=[lat, long], radius=5,
                            tooltip = popup_text, fill=True, color=imeca_colors(pollutant, c_value),
                            fill_opacity=0.65).add_to(folium_map)

    return(folium_map)


def compare_mx_aqip(pollutant, date, year_limit=2020, zoom=5):
    """Creates a map with the analysis of the average between the week previous to the input date 
        and the weeek of the previous year for a selected pollutant

    Args:
        pollutant {str} -- pollutant to be plotted
        date {str} -- date to be analyzed in format yyyy-mm-dd
        year_limit{int} -- int with the limit year for the city's database, set to 2020 by default
        zoom{int} -- zoom start value for the folium_map

    Returns:
        folium_map -- folium map where a blue marker indicates a smaller value of the input date concentration and, 
                        the bigger the marker the larger the concentration
    """

    dir_ext = '../data/external/INEGI/'
    
    dir_pcs = '../data/processed/'
    
    mx_mun = pd.read_csv(dir_ext+'CentroidMunicipalities_INEGI19_v1.csv', encoding ='latin_1')
    
    aqip_mx = pd.read_csv(dir_pcs+'aqip/MX_'+pollutant+'_2017-'+str(year_limit)+'.csv', encoding='latin_1').set_index('Date')
    
    prev_year = str(int(date[:4])-1)+date[4:]
    
    centro_lat, centro_lon = 22.396092, -101.731430 #map center

    #Creates folium map
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=zoom,
                            tiles = 'cartodb positron')
    
    cty_aqip = [c for c in aqip_mx.columns]
    
    for i in range(1,len(cty_aqip)):
        
        city = cty_aqip[i]
        
        #specify names for Oaxaca and Mexico city
        if city == 'Oaxaca':
            city = 'Oaxaca de Juárez'
        
        elif city == 'Mexico City':
            city = 'Ciudad de México'
        
        c_current = aqip_mx.loc[date,cty_aqip[i]]
        c_prev = aqip_mx.loc[prev_year,cty_aqip[i]]
        c_graph = (c_current - c_prev)/c_prev
        
        lat = float(mx_mun[mx_mun['NOMGEO']==city].lat)
        
        long = float(mx_mun[mx_mun['NOMGEO']==city].long)
 
        #City centroids with name, latitude, longitude, pollutant and concentration
        popup_text = f"<b> Nombre: </b> {city} <br> <b> Latitud: </b> {lat:.5f} <br> <b> Longitud: </b> {long:.5f} <br> <b> Contaminante: </b> {pollutant} <br> <b> Cambio: </b> {c_graph} <br>"

        #adds points to map
        folium.CircleMarker(location=[lat, long], radius=5,
                            tooltip = popup_text, fill=True, color=clr_change(c_graph),
                            fill_opacity=0.65).add_to(folium_map)

    return(folium_map)



def aqip_yearly(month_limit=5, year_limit=2020):
    """Creates a graph that compares the air quality data for each pollutant from January to month_limit,
        set by default to 5 (May)from 2017 to year_limit, set by default to 2020

    Args:
        year_limit{int} -- int with the limit year for the city's database, set to 2020 by default
        month_limit {int} -- int with limit month to be analyzed, set to 5 (May) by default

    Returns:
        plot -- line plot with the data from AQIP and air quality stations
    """
    dir_pcs = '../data/processed/aqip/'
    dir_fig = '../output/figures/aqip_yearly/' #output directory
    
    
    for i in range(5):
        
        aqip_mx = pd.read_csv(dir_pcs+'MX_'+src.pollutant(i)+'_'+str(2017)+'-'+str(year_limit)+'_raw.csv',
                 encoding='latin_1') #DataFrame with air quality concentrations by week and city
        
        aqip_mx['Date'] = pd.to_datetime(aqip_mx['Date'])
        
        cty_aqip = src.city_valid_aqip(src.pollutant(i)) #creates a list with cities above treshold
        
        outlier = src.catch_outliers(src.pollutant(i)) #outlier limit
        
        plt.figure(figsize=(15,7.5)) #figure size
        
        
        for c in cty_aqip:
        
            ax = plt.gca()

            for y in range(2017, year_limit+1):
                
                pt=aqip_mx[aqip_mx['Date'].dt.year==y]
                pt= pt.set_index(pt['Date'].dt.strftime('%m-%d'))
                pt = pd.DataFrame(pt[c])
                
                pt = pt[pt[c]<=outlier] #filters data above outliers
                
                pt.plot(y=c,ax=ax, label=y)
    
            ticklabels=['Ene','Feb','Mar','Abr','May','Jun','Jul',
                        'Agu','Sep','Oct','Nov','Dic']
            tickplace = [15+30*n for n in range(month_limit+1)] #xaxis placement
            ax.set_xticks(tickplace)
            ax.set_xticklabels(ticklabels[:month_limit+1]) #add monthlabels to the xaxis

            plt.ylabel('Concentración: '+src.pollutant(i))
            plt.xlabel('Fecha')

            plt.savefig(dir_fig+c+'_Year_Compare_'+src.pollutant(i)+'.png', dpi=300) #saves figure

            ax.clear()

def hex_plot(pollutant, city, station, ax, gdf_data, gdf_boundary, column , title,save_png=False, save_pdf=False,show=False, name='plot',dpi=300,transparent=True, close_figure=True):
    """
    Plot hexbin geoDataFrames to create the accesibility plots, based on hex_plot 
    from Luis Natera in Observatorio-Ciudades/accesibilidad-urbana

    Arguments:
        pollutant {str} -- pollutant to be plotted
        city {str} -- code for the city to be analyzed, for example: cdmx
        station {gdf} -- gdf with stations within the city
        ax {matplotlib.axes} -- ax to use in the plot
        gdf_data {geopandas.GeoDataFrame} -- geoDataFrame with the data to be plotted
        gdf_boundary {geopandas.GeoDataFrame} -- geoDataFrame with the boundary to use 
        gdf_edges {geopandas.GeoDataFrame} -- geoDataFrame with the edges (streets)
        column {geopandas.GeoDataFrame} -- column to plot from the gdf_data geoDataFrame
        title {str} -- string with the title to use in the plot

    Keyword Arguments:
        save_png {bool} -- save the plot in png or not (default: {False})
        save_pdf {bool} -- save the plot in pdf or not (default: {False})
        show {bool} -- show the plot or not (default: {False})
        name {str} -- name for the plot to be saved if save=True (default: {plot})
        dpi {int} -- resolution to use (default: {300})
        transparent {bool} -- save with transparency or not (default: {True})
    """
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    gdf_data[gdf_data[column]<=0].plot(ax=ax,color='#2b2b2b', alpha=0.95, linewidth=0.1, edgecolor='k', zorder=0)
    gdf_data['color'] = gdf_data[column].apply(lambda c :imeca_colors(pollutant,c))
    gdf_data[gdf_data[column]>0].plot(ax=ax,column=column, cmap='viridis',vmin=0, vmax=src.p_limits(pollutant),
                                      zorder=1,legend=True,cax=cax,legend_kwds={'label':'Concentración'+src.p_unit(pollutant),'orientation': "horizontal"})
    
    
    gdf_boundary.boundary.plot(ax=ax,color='#f8f8f8',zorder=2,linestyle='--',linewidth=0.5)
    
    
    station_gdf = gpd.GeoDataFrame(
        station[station['city']==src.city_name(city)], geometry=gpd.points_from_xy(station[station['city']==src.city_name(city)].long, 
                                                                                         station[station['city']==src.city_name(city)].lat))
    
    station_gdf.crs = {'init':' epsg:4326'}
    
    station_filter = gpd.clip(station_gdf, gdf_boundary, keep_geom_type=False)
    
    station_filter.plot(ax=ax, color='#bcbcbc', alpha = 0.75, markersize = 3, label = station_gdf['nombre'])

    
    ax.set_title(f'{title}',fontdict={'fontsize':20})

    ax.axis('off')
    if save_png:
        plt.savefig('../output/figures/hex/{}.png'.format(name),dpi=dpi,transparent=transparent)
    if save_pdf:
        plt.savefig('../output/figures/hex/{}.pdf'.format(name))
    if close_figure:
        plt.close()
    if show:
        plt.show()