################################################################################
# Module: Data gathering and treatment
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
dir_raw_aqip = dir_grl + 'processed\\aqip\\'
dir_raw_cdmx = dir_grl + 'processed\\cdmx\\'
dir_pcs_cat = dir_grl + 'processed\\aqip_cdmx\\'
dir_raw = dir_grl + 'raw\\'
dir_raw_grl = dir_raw + 'Grl\\'


#Descarga datos de la ciudad, contaminantes y cantidad de datos establecidos
ciudad = 'Guadalajara'
contaminante = ['O3', 'PM10', 'CO']
num_datos = 10000

#Parametros de contaminantes
param = ['CO','NO2', 'O3','PM10','PM25','SO2']

#Funcion para guardar json con informacion de contaminantes a csv
def parse_mediciones_json(json_file):
    
    with open (json_file,'r') as aux:
        results = json.load(aux)['results']
        
    pre_data=[]
    
    for r in results:
        
        aux = pd.DataFrame.from_dict(r,orient='index').T
        pre_data.append(aux)
    
    if len(pre_data)>0:
        pre_data = pd.concat(pre_data,ignore_index=True)
        return pre_data

#Checa si existe la carpeta de la ciudad y contaminantes y los crea si no existen
if not os.path.isdir(direccion+ciudad): 
    os.mkdir(direccion+ciudad) 
    for c in param: os.mkdir(dir_raw+ciudad+'\\'+c)


#Itera sobre la lista de contaminantes y obtiene ese parametro para la ciudad establecida
for p in param:
    filename = ciudad+'_'+p
    filename = direccion+ciudad+'\\'+p+'\\'+filename
    
    data_api = client.makeCall('sinaica',{'pageSize':num_datos, 'city':ciudad, 'parametro':p})
        
    with open (filename,'w') as outfile:
        json.dump(data_api,outfile)
        
    sinaica_mediciones = parse_mediciones_json(filename)
    sinaica_mediciones.to_csv(filename+'.csv', index=False)

def est_csv():
    """Downloads csv with information about Mexican air quality stations using SINAICA api

    """
        
    parametros_request = client.makeCall('sinaica-estaciones',{'pageSize':200})

    estaciones = []
    #Obtiene datos de todas las estaciones para despues iterar sobre ellas
    for v in parametros_request['results']:
        aux = pd.DataFrame.from_dict(v,orient='index').T
        estaciones.append(aux)

    estaciones = pd.concat(estaciones, ignore_index=True)

    #Quita las estaciones que esten fuera de Mexico
    mask = (estaciones.lat.between(14, 34.5)) & (estaciones.long.between(-120, -70))
    estaciones = estaciones[mask]

    filename = dir_raw_grl+'estaciones'

    estaciones.to_csv (r''+filename+'.csv', index = False, header=True)

#Extracts data from cdmx database
def cdmx_data():
    """Merges the databases from Mexico City air quality stations into a single csv

    Returns:
        csv -- csv with all the data from air quality stations
    """
    all_data = pd.DataFrame()
    for year in years:
        for p in param:
            
            data = pd.read_excel(dir_raw+str(year)[-2:]+'RAMA\\'+str(year)+p+'.xls').replace(-99,np.NaN)
            data['PARAM']=p
            data = data.set_index(['PARAM','FECHA','HORA'])
            all_data = all_data.append(data)
    
    filename = dir_pcs + str(years[0])+'-'+str(years[len(years)-1])
    all_data.to_csv (r''+filename+'.csv', index = True, header=True)

def res_cdmx():
    res_data = pd.read_csv(dir_pcs + str(years[0])+'-'+str(years[len(years)-1])+'.csv', index_col = [0,1])
    res_data = res_data.groupby(['PARAM','FECHA']).mean()
    
    filename = dir_pcs +'res_'+ str(years[0])+'-'+str(years[len(years)-1])
    res_data.to_csv (r''+filename+'.csv', index = True, header=True)
    
    
def cdmx_daily_mean():
    cdmx_mean_data = pd.read_csv(dir_pcs +'res_'+ str(years[0])+'-'+str(years[len(years)-1])+'.csv', index_col = [0,1]).median(axis=1)
    
    cdmx_mean_data.to_csv(dir_pcs +'median_res_'+ str(years[0])+'-'+str(years[len(years)-1])+'.csv')
    
    return (cdmx_mean_data)


def o3_conc(x):
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
        
    return (conc*1000)

def co_conc(x):
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
    
#Extracts data from aqip database
def aqip_data():
    
    all_data = pd.DataFrame()
    
    for file in os.listdir(dir_raw):

        filename = dir_raw + file
        
        data_aqip = pd.DataFrame()
        
        data_aqip = pd.read_csv(filename, skiprows=4)
        
        data_aqip['Specie'] = data_aqip['Specie'].str.upper()
        
        data_aqip = data_aqip.set_index(['Specie'])
        
        data_aqip = data_aqip[data_aqip['Country']=='MX'].drop(['Country'], axis=1)
        
        all_data = all_data.append(data_aqip)
        
    
    cond = [all_data.index == 'O3', all_data.index == 'CO', all_data.index == 'PM10', 
           all_data.index == 'PM25', all_data.index == 'NO2', all_data.index == 'SO2']
    
    choice = [all_data['median'].apply(o3_conc), all_data['median'].apply(co_conc), 
             all_data['median'].apply(pm10_conc), all_data['median'].apply(pm25_conc),
             all_data['median'].apply(no2_conc), all_data['median'].apply(so2_conc)]
    
    all_data['c_median'] = np.select(cond, choice)
    
    all_data = all_data.reset_index().set_index(['City','Specie','Date'])

    all_data.to_csv(dir_pcs +'MX_2015_2020.csv')
