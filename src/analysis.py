################################################################################
# Module: Analysis data
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 17/07/2020
################################################################################

#from pathlib import Path
import json
import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import src
from math import sqrt
import geopandas as gpd


#Tests the data from aqip compared to cdmx
def t_test(df_aqip, df_mx):
    """Calculates t test and p value for two air quality dataframes

    Args:
        df_aqip {dataframe} -- dataframe with concentrations for mexican cities from air quality index project
        df_mx {dataframe} -- dafaframe with concentrations from stations for mexican cities

    Returns:
        tuple -- tuple with t and p values for the compared dataframes
    """
    #Calculate t and p values
    t, p = stats.ttest_ind(df_mx, df_aqip, equal_var=False)
    
    return (t, p)



def aqip_city_mrg(city):
    """Function that creates a merged csv from dataframes from median concentrations 
        for air quality index project and mexican cities stations

    Args:
        city {str} -- code for the city that will be merged
    """

    dir_pcs = '../data/processed/' #Directory for processed data

    if not os.path.isdir(dir_pcs+'aqip_'+city): 
        os.mkdir(dir_pcs+city) 

    dir_pcs_cat = dir_pcs+'aqip_'+city #Directory to save concatenation

    mx = pd.read_csv(dir_pcs+city+'/'+'median_res_2017-2020.csv') #csv with medians from city's air quality stations

    aqip = pd.read_csv(dir_pcs+'aqip/' +'MX_2015_2020.csv', index_col=[0]) #csv with medians from aqip database

    aqip = aqip.loc[src.city_name(city)] #filters aqip data according to city

    compare = pd.merge(aqip, mx, how='inner', left_on=['Specie','Date'], right_on=['PARAM','FECHA']) #merges csvs

    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                   'Date':'Fecha',
                                                                                                   'c_median':'aqip_median',
                                                                                                   '0':'mx_median'})
    compare.to_csv(dir_pcs_cat +city+'_AQIP.csv') #saves merged csv

    
def data_valid(city):
    """Function that compares if the air quality data from mexican monitoring stations and
        the air quality index project are statistically different

    Args:
        city {str} -- city code for the city to by analyzed

    Return:
        str -- string with t and p values for the analyzed data
    """

    dir_pcs = '../data/processed/' #Directory for processed data
    dir_pcs_cat = dir_pcs+'aqip_'+city #Directory to save concatenation

    valid_check = pd.read_csv(dir_pcs_cat +city+'_AQIP.csv') #DataFrame with medians from AQIP and air quality stations
    
    df_aqip = valid_check[['Contaminante','aqip_median']] #DataFrame with aqip median
    df_mx = valid_check[['Contaminante','mx_median']] #Dataframe with city's air quality stations median
    
    
    for i in range(5):
        
        #calls function that calculates t and p value

        t,p = t_test(df_aqip[df_aqip['Contaminante']==src.pollutant(i)].drop(columns=['Contaminante']),
                    df_mx[df_mx['Contaminante']==src.pollutant(i)].drop(columns=['Contaminante']))

        return ('For: '+src.pollutant(i)+' t value is: '+str(t)+' and p value is: '+str(p))

def airquality_average(city, month_limit=5, year_limit=2020):
    """Function that creates separate csv from month 1 (january) to limit_month of the yearly data available, starting at 2017
        and ending at year_limit, set to default at 2020

    Args:
        city {str} -- string containing city code to be analyzed
        year_limit {int} -- int with limit year to be analyzed, set to 2020 by default
        month_limit {int} -- int with limit month to be analyzed, set to 5 (May) by default

    Returns:
        csv: individual csv for each pollutant with the average data by week of the first four months of the yearly data available
    """
    dir_pcs_mx = '../data/processed/'+city+'/'  #Directory for processed data

    data_csv = dir_pcs_mx+city+'_2017-'+str(year_limit)+'.csv' #csv with pollutant data from city's air quality stations
    
    #reads csv as dataframe and calculates daily averages pollutants concentrations
    data_bydate = pd.read_csv(data_csv).set_index(['FECHA','PARAM']).groupby(level=('FECHA','PARAM')).mean().reset_index()
    
    data_bydate['FECHA'] = pd.to_datetime(data_bydate['FECHA']) #sets column as datetime
    
    #creates a new dataframe with daily averages for the specified months
    for m in range(1,month_limit+1):
        if m == 1: 
            filter_month=data_bydate[data_bydate['FECHA'].dt.month==m]

        else:

            month_tmp = data_bydate[data_bydate['FECHA'].dt.month==m]


            filter_month = filter_month.append(month_tmp)
    
    #creates csv for daily averages for each pollutant
    for i in range(5):
        
        data_bydateParam = filter_month[filter_month['PARAM']==src.pollutant(i)].set_index('FECHA')
        
        data_bydateParam = data_bydateParam.rolling(7, min_periods=1).mean()
        
        #converts ppm to ppb for O3, NO2 and SO2
        if src.pollutant(i)!= 'PM10' or src.pollutant(i) != 'CO':
            data_bydateParam = data_bydateParam*1000
        
        data_bydateParam.to_csv(data_csv[:-4]+'_'+src.pollutant(i)+'.csv')

def interpolate_tohex(city, pollutant, date, stations, city_area, cellsize, year_limit):
    """Function that creates a folium map with user specified city, pollutant and date and interpolates valid values


        Args:
            city {str} -- code for the city to be analyzed, for example: cdmx
            pollutant {str} -- pollutant to be plotted
            date {str} -- date to be analyzed in format yyyy-mm-dd
            station {gdf} -- gdf with stations within the city
            city_area {gdf} -- gdf with area of interpolation
            cell_size{float} -- cell size for the interpolation in degrees, set to 0.01 by default
            year_limit{int} -- int with the limit year for the city's database, set to 2020 by default

        Returns:
            gdf -- gdf with interpolated concentration for the specified pollutant
    """

    dir_pcs = '../data/processed/'    

    data_csv = dir_pcs+city+'/'+city+'_2017-'+str(year_limit)+'_'+pollutant+'.csv'
    
    data_bydateParam = pd.read_csv(data_csv).set_index('FECHA')
    
    #lists to append valid values of lat and long for interpolation
    
    x = []
    y = []
    
    for i, est in stations[stations['city']==src.city_name(city)].iterrows():

                est_code = stations.loc[(i),'codigo']
                c_value = data_bydateParam.loc[(date),est_code]
                
                if pd.notna(c_value):
                    x.append(est.long)
                    y.append(est.lat)
    
    #Registers the boundries coordinates for the interpolation
    min_x, min_y, max_x, max_y = city_area.geometry.total_bounds

    #Valor de potencia
    p = 2

    #x and y values for the start of the interpolation
    xidw=min_x
    yidw=min_y

    #Variables for interpolation
    dividendo = 0
    divisor = 0
    idw=[]

    #interpolates the data
    while xidw <= max_x:
        while yidw <= max_y:
            for i, est in stations[stations['city']==src.city_name(city)].iterrows():

                est_code = stations.loc[(i),'codigo']
                c_value = data_bydateParam.loc[(date),est_code]

                if pd.notna(c_value):
                    dividendo = (c_value/(sqrt((est.long-xidw)**2+(est.lat-yidw)**2)**(p)))+ dividendo
                    divisor = (1/(sqrt((est.long-xidw)**2+(est.lat-yidw)**2)**(p))) + divisor

            concentracion = dividendo/divisor

            idw.append([yidw,xidw,concentracion])
            yidw = yidw + cellsize
            dividendo = 0
            divisor = 0  
        xidw = xidw + cellsize
        yidw = min_y

    #adds interpolated data to DataFrame
    inter = pd.DataFrame(idw, columns=['lat','long','conc'])
    
    #transforms DataFrame to GeoDataFrame
    inter_gdf = gpd.GeoDataFrame(
        inter, geometry=gpd.points_from_xy(inter.long, inter.lat))
    
    inter_gdf.crs = {'init':' epsg:4326'}
    
    return(inter_gdf)