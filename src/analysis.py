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


dir_grl = 'D:\\Users\\edgar\\Source\\Repos\\Observatorio-Ciudades\\calidad-aire\\data\\'
dir_pcs_aqip = dir_grl + 'processed\\aqip\\'
dir_pcs_cdmx = dir_grl + 'processed\\cdmx\\'
dir_pcs_cat = dir_grl + 'processed\\aqip_cdmx\\'
fig = 'D:\\Users\\edgar\\Source\\Repos\\Observatorio-Ciudades\\calidad-aire\\output\\figures\\aqip_analysis\\'

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
    
    compare = pd.read_csv(dir_pcs_cat +'MexicoCity_AQIP_CDMX.csv')
    
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
        
        print ('For: '+c+' t value is: '+str(t)+' and p value is: '+str(p))