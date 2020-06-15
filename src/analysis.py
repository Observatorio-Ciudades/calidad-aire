################################################################################
# Module: Analysis data
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 07/06/2020
################################################################################

from pathlib import Path
import json
import os
from datosgobmx import client
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

#test
dir_grl = 'D:\\Users\\edgar\\Source\\Repos\\Observatorio-Ciudades\\calidad-aire\\data\\'
dir_pcs_aqip = dir_grl + 'processed\\aqip\\'
dir_pcs_cdmx = dir_grl + 'processed\\cdmx\\'
dir_pcs_cat = dir_grl + 'processed\\aqip_cdmx\\'
fig = 'D:\\Users\\edgar\\Source\\Repos\\Observatorio-Ciudades\\calidad-aire\\output\\figures\\aqip_analysis\\'

param = ['CO','NO2', 'O3','PM10','PM25','SO2']

#Tests the data from aqip compared to cdmx

def t_test(df_aqip, df_cdmx):
    t, p = stats.ttest_ind(df_cdmx, df_aqip, equal_var=False)
    
    return (t, p)

def aqip_cdmx():
    cdmx = pd.read_csv(dir_pcs_cdmx +'median_res_2017-2020.csv')
    aqip = pd.read_csv(dir_pcs_aqip +'MX_2015_2020.csv', index_col=[0])

    aqip = aqip.loc['Mexico City']

    compare = pd.merge(aqip, cdmx, how='inner', left_on=['Specie','Date'], right_on=['PARAM','FECHA'])

    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                   'Date':'Fecha',
                                                                                                   'c_median':'aqip_median',
                                                                                                   '0':'cdmx_median'})
    compare.to_csv(dir_pcs_cat +'MexicoCity_AQIP_CDMX.csv')
    
def plt_aq(c):

    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                   'Date':'Fecha',
                                                                                 
    
    compare=pd.read_csv(dir_pcs_cat +'MexicoCity_AQIP_CDMX.csv')
    
    ax = plt.gca()
    compare[compare['Contaminante']==c].plot(kind='scatter', x='Fecha',y='cdmx_median', color='green', ax=ax)
    compare[compare['Contaminante']==c].plot(kind='scatter', x='Fecha',y='aqip_median', color='orange',
                                             alpha = 0.75, ax=ax)
    plt.ylabel('Concentration: '+c)
    
    plt.savefig(fig+c+'_x1.png')
    
    plt.show()
    
def data_valid():
    
    valid_check = pd.read_csv(dir_pcs_cat +'MexicoCity_AQIP_CDMX.csv')
    
    df_aqip = valid_check[['Contaminante','aqip_median']]
    df_cdmx = valid_check[['Contaminante','cdmx_median']]
    
    df_aqip['Contaminante']
    
    for c in param:
        
        #print (df_aqip[df_aqip['Contaminante']==c].drop(columns=['Contaminante']))
        
        t,p = t_test(df_aqip[df_aqip['Contaminante']==c].drop(columns=['Contaminante']),
                     df_cdmx[df_cdmx['Contaminante']==c].drop(columns=['Contaminante']))
        
        print ('For: '+c+' t value is: '+str(t)+' and p value is: '+str(p))'PARAM','FECHA'])

    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                   'Date':'Fecha',
                                                                                 

def airquality_average(data_csv):
    """Function that creates separate csv for the first four months of the yearly data available.

    Args:
        data_csv (str): string containing the directory and name of the csv file

    Returns:
        csv: individual csv for each pollutant with the average data by week of the first four months of the yearly data available.
    """
    
    month = [1,2,3,4]
    
    data_bydate = data_csv.groupby(level=('FECHA','PARAM')).mean().reset_index()
    data_bydate['FECHA'] = pd.to_datetime(data_bydate['FECHA'])
    
    for m in month:
        if m == 1: 
            filter_month=data_bydate[data_bydate['FECHA'].dt.month==m]

        else:

            month_tmp = data_bydate[data_bydate['FECHA'].dt.month==m]


            filter_month = filter_month.append(month_tmp)
    
    for p in param:
        
        data_bydateParam = filter_month[filter_month['PARAM']==p].set_index('FECHA')
        
        data_bydateParam = data_bydateParam.rolling(7, min_periods=1).mean()
        
        data_bydateParam.to_csv(dir_data[:-4]+'_'+p+'.csv')
        
    #return (data_bydateParam)