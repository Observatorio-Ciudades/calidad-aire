################################################################################
# Module: Analysis data
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 15/06/2020
################################################################################

from pathlib import Path
import json
import os
from datosgobmx import client
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt


#Tests the data from aqip compared to cdmx
def t_test(df_aqip, df_mx):
    """Calculates t test and p value for two air quality dataframes.

    Args:
        df_aqip (dataframe): dataframe with concentrations for mexican cities from air quality index project.
        df_mx (dataframe): dafaframe with concentrations from stations for mexican cities.

    Returns:
        [tuple]: tuple with t and p values for the compared dataframes.
    """

    t, p = stats.ttest_ind(df_mx, df_aqip, equal_var=False)
    
    return (t, p)

def pollutant(p):
    """Function that returns a str with a pollutant.

    Args:
        p (int): values from 0 to 5 for list place.

    Returns:
        str: pollutant.
    """
    #Parametros de contaminantes
    param = ['CO','NO2', 'O3','PM10','PM25','SO2']
    return (param[p])

def aqip_mx(city):

    """Merges dataframes from csv with air quality daily median concentrations for
        air quality index project and mexican cities stations
    """

    dir_pcs = '../data/processed/'
    dir_pcs_aqip = '../data/processed/aqip/'

    city_dict = {'gdl':'Guadalajara', 'cmdx':'Mexico City'}

    if not os.path.isdir(dir_pcs+'aqip_'+city): 
        os.mkdir(dir_pcs+city) 

    dir_pcs_cat = dir_pcs+'aqip_'+city #Directory to save concatenation

    mx = pd.read_csv(dir_pcs+city+'/'+'median_res_2017-2020.csv')
    aqip = pd.read_csv(dir_pcs_aqip +'MX_2015_2020.csv', index_col=[0])

    aqip = aqip.loc[city_dict[city]]

    compare = pd.merge(aqip, mx, how='inner', left_on=['Specie','Date'], right_on=['PARAM','FECHA'])

    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                   'Date':'Fecha',
                                                                                                   'c_median':'aqip_median',
                                                                                                   '0':'mx_median'})
    compare.to_csv(dir_pcs_cat +city+'_AQIP.csv')

    
def data_valid(city):
    """Function that compares if the air quality data from mexican monitoring stations and
        the air quality index project are statistically different.

    Args:
        city (str): city code for the city to by analyzed.
    """

    dir_pcs = '../data/processed/'
    dir_pcs_cat = dir_pcs+'aqip_'+city #Directory to save concatenation

    valid_check = pd.read_csv(dir_pcs_cat +city+'_AQIP.csv')
    
    df_aqip = valid_check[['Contaminante','aqip_median']]
    df_mx = valid_check[['Contaminante','mx_median']]
    
    df_aqip['Contaminante']
    
    for i in range(6):
        
        #print (df_aqip[df_aqip['Contaminante']==c].drop(columns=['Contaminante']))
        
        t,p = t_test(df_aqip[df_aqip['Contaminante']==pollutant(i)].drop(columns=['Contaminante']),
                    df_mx[df_mx['Contaminante']==pollutant(i)].drop(columns=['Contaminante']))

        print ('For: '+pollutant(i)+' t value is: '+str(t)+' and p value is: '+str(p))

def airquality_average(city):
    """Function that creates separate csv for the first four months of the yearly data available.

    Args:
        data_csv (str): string containing the directory and name of the csv file

    Returns:
        csv: individual csv for each pollutant with the average data by week of the first four months of the yearly data available.
    """
    dir_pcs_mx = '../data/processed/'+city+'/'
    data_csv = dir_pcs_mx+city+'_2017-2020.csv'

    if city == 'cdmx':
        data_csv = '../data/processed/'+city+'/'+city+'_2017-2020_filtered.csv'
    
    month = [1,2,3,4]
    
    data_bydate = data_csv.groupby(level=('FECHA','PARAM')).mean().reset_index()
    data_bydate['FECHA'] = pd.to_datetime(data_bydate['FECHA'])
    
    for m in month:
        if m == 1: 
            filter_month=data_bydate[data_bydate['FECHA'].dt.month==m]

        else:

            month_tmp = data_bydate[data_bydate['FECHA'].dt.month==m]


            filter_month = filter_month.append(month_tmp)
    
    for i in range(6):
        
        data_bydateParam = filter_month[filter_month['PARAM']==pollutant(i)].set_index('FECHA')
        
        data_bydateParam = data_bydateParam.rolling(7, min_periods=1).mean()
        
        data_bydateParam.to_csv(data_csv[:-4]+'_'+pollutant(i)+'.csv')
        
    #return (data_bydateParam)
