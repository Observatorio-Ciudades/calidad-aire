################################################################################
# Module: Data gathering and treatment
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
import xlrd


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

#Funcion para guardar json con informacion de contaminantes a csv
def parse_mediciones_json(json_file):
    """Function that converts json files to csv.

    Args:
        json_file ([json]): File in json.

    Returns:
        [csv]: json convedescriptionrted to csv.
    """
    
    with open (json_file,'r') as aux:
        results = json.load(aux)['results']
        
    pre_data=[]

    for r in results:
        
        aux = pd.DataFrame.from_dict(r,orient='index').T
        pre_data.append(aux)
    
    if len(pre_data)>0:
        pre_data = pd.concat(pre_data,ignore_index=True)
        return (pre_data)


def data_gdl(city, num_datos):
    """Function that downloads csv with from SINAICA for a given city.

    """
    dir_raw = '../data/raw/'

    city_dict = {'gdl':'Guadalajara'}

    #Checa si existe la carpeta de la ciudad y contaminantes y los crea si no existen
    if not os.path.isdir(dir_raw+city): 
        os.mkdir(dir_raw+city) 
        for i in range(6): os.mkdir(dir_raw+city+'/'+pollutant(i))


    #Itera sobre la lista de contaminantes y obtiene ese parametro para la ciudad establecida
    for i in range(6):
        filename = city+'_'+pollutant(i)
        filename = dir_raw+city+'/'+pollutant(i)+'/'+filename
        
        data_api = client.makeCall('sinaica',{'pageSize':num_datos, 'city':city_dict[city], 'parametro':pollutant(i)})
            
        with open (filename,'w') as outfile:
            json.dump(data_api,outfile)
            
        sinaica_mediciones = parse_mediciones_json(filename)
        sinaica_mediciones.to_csv(filename+'.csv', index=False)

def est_csv():
    """Downloads csv with information about Mexican air quality stations using SINAICA api

    """
        
    parametros_request = client.makeCall('sinaica-estaciones',{'pageSize':200})
    dir_raw_grl = '../data/raw/Grl/'

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
def merge_aq(city):
    """Merges the databases from a given city air quality stations into a single csv

    Returns:
        csv -- csv with all the data from air quality stations
    """
    dir_raw = '../data/raw/'
    dir_pcs = '../data/processed/'

    years = [2017, 2018, 2019] #Years to be merged
    
    all_data = pd.DataFrame()
    for year in years:
        
        #for i in range(5):    
            #data = pd.read_excel(dir_raw+city+str(year)[-2:]+'RAMA\\'+str(year)+pollutant(i)+'.xls').replace(-99,np.NaN)
        data = pd.read_csv(dir_raw+city+'/stack/'+str(year)+'.csv').replace(r'^\s*$',np.nan,regex=True)
        data = data.set_index(['PARAM','FECHA'])
        all_data = all_data.append(data)
    
    filename = dir_pcs + city + '/' + city + '_' + str(years[0])+'-'+str(years[len(years)-1])
    all_data.to_csv (r''+filename+'.csv', index = True, header=True)

def res_aqdata(city):
    """Groups data from air quality stations by date and parameter for every station.

    Args:
        city (str): city code to by analyzed.
    """

    dir_pcs = '../data/processed/'

    years = [2017, 2018, 2019, 2020] #Years to be summarized

    res_data = pd.read_csv(dir_pcs +city + str(years[0])+'-'+str(years[len(years)-1])+'.csv', index_col = [0,1])
    res_data = res_data.groupby(['PARAM','FECHA']).mean()
    
    filename = dir_pcs +'res_'+ str(years[0])+'-'+str(years[len(years)-1])
    res_data.to_csv (r''+filename+'.csv', index = True, header=True)
    
    
def aq_daily_median(city):
    """Calculates the median by day for a given city and pollutant.

    Args:
        city (str): city code to calculate median

    Returns:
        dataframe: returns the dataframe for the date and calculated median.
    """

    dir_pcs = '../data/proccessed/'

    years = [2017, 2018, 2019, 2020] #Years to be referenced

    aq_median_data = pd.read_csv(dir_pcs +city+'res_'+ str(years[0])+'-'+str(years[len(years)-1])+'.csv', index_col = [0,1]).median(axis=1)
    
    aq_median_data.to_csv(dir_pcs+city+'median_res_'+ str(years[0])+'-'+str(years[len(years)-1])+'.csv')
    
    return (aq_median_data)


def o3_conc(x):
    """Calculates the concentration of a pollutant based on air quality index.

    Args:
        x (int): air quality index of the pollutant

    Returns:
        float: concentration of the pollutant
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
        
    return (conc*1000)

def co_conc(x):
    """Calculates the concentration of a pollutant based on air quality index.

    Args:
        x (int): air quality index of the pollutant

    Returns:
        float: concentration of the pollutant
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
    """Calculates the concentration of a pollutant based on air quality index.

    Args:
        x (int): air quality index of the pollutant

    Returns:
        float: concentration of the pollutant
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
    """Calculates the concentration of a pollutant based on air quality index.

    Args:
        x (int): air quality index of the pollutant

    Returns:
        float: concentration of the pollutant
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
    """Calculates the concentration of a pollutant based on air quality index.

    Args:
        x (int): air quality index of the pollutant

    Returns:
        float: concentration of the pollutant
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
    """Calculates the concentration of a pollutant based on air quality index.

    Args:
        x (int): air quality index of the pollutant

    Returns:
        float: concentration of the pollutant
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
    
#Extracts data from aqip database
def aqip_data():
    """Function that extracts data for mexican city from the Air Quality Index Project database.

    """
    dir_raw_aqip = '../data/raw/AirQualityIndexProject/world_data/'
    dir_pcs_aqip = '../data/processed/aqip/'
    
    all_data = pd.DataFrame()
    
    for file in os.listdir(dir_raw_aqip):

        filename = dir_raw_aqip + file
        
        data_aqip = pd.DataFrame()
        
        data_aqip = pd.read_csv(filename, skiprows=4)
        
        data_aqip['Specie'] = data_aqip['Specie'].str.upper()
        
        data_aqip = data_aqip.set_index(['Specie'])
        
        data_aqip = data_aqip[data_aqip['Country']=='MX'].drop(['Country'], axis=1)
        
        all_data = all_data.append(data_aqip)
        
    #Condition that selects pollutant
    cond = [all_data.index == 'O3', all_data.index == 'CO', all_data.index == 'PM10', 
           all_data.index == 'PM25', all_data.index == 'NO2', all_data.index == 'SO2']
    
    #Choice that dictates what happends for each case
    choice = [all_data['median'].apply(o3_conc), all_data['median'].apply(co_conc), 
             all_data['median'].apply(pm10_conc), all_data['median'].apply(pm25_conc),
             all_data['median'].apply(no2_conc), all_data['median'].apply(so2_conc)]
    
    #Calculates a new column with the data converted from 
    #air quality index to concentration by pollutant

    all_data['c_median'] = np.select(cond, choice)
    
    all_data = all_data.reset_index().set_index(['City','Specie','Date'])

    all_data.to_csv(dir_pcs_aqip +'MX_2015_2020.csv')
    
    
def gdl_data ():
    """Merges and adjusts format for SIMAJ database for Guadalajara's stations.
    
    """

    dir_gdl = '../data/raw/gdl/'
    
    est_dict = {'ÁGUILAS':'AGU', 'ATEMAJAC':'ATM', 'CENTRO':'CEN', 
                'LAS PINTAS':'PIN', 'LOMA DORADA':'LDO', 'MIRAVALLE':'MIR', 'OBLATOS':'OBL', 
                'SANTA FE':'SFE', 'TLAQUEPAQUE':'TLA', 'VALLARTA':'VAL'}
    
    for file in os.listdir(dir_gdl):

        f_check = os.path.join(dir_gdl,file)

        if os.path.isfile(f_check):

            xls = xlrd.open_workbook(r''+dir_gdl+file, on_demand=True)
            sheets = xls.sheet_names()

        else:
            continue
        
        year = file[6:10]
        
        print (year)
        
        df = pd.DataFrame(columns=['O3','CO','PM10','SO2','NO2'])

        df['FECHA'] = pd.date_range(start = pd.Timestamp(year), 
                                   end = pd.Timestamp(year) + pd.tseries.offsets.YearEnd(0),
                                   freq = 'D')

        df = df.set_index('FECHA')
        df = df.stack(dropna=False)
        all_data = pd.DataFrame(df)
        all_data = all_data.rename_axis(index=['FECHA','PARAM'])
        all_data = all_data.drop(columns=[0])
        
        #print(all_data)

        for s in sheets:

            gdl_data = pd.read_excel(dir_gdl+file, sheet_name = s).rename(columns={'Fecha':'FECHA',
                                                                                   'Hora':'HORA'}).replace(r'^\s*$', 
                                                                                                           np.nan, 
                                                                                                           regex=True)
            gdl_data.columns = [col.strip() for col in gdl_data.columns]
            
            gdl_data = gdl_data[['FECHA','O3','NO2','SO2','PM10','CO']]

            gdl_data['FECHA'] = gdl_data['FECHA'].dt.date

            gdl_stack = pd.DataFrame(gdl_data.set_index(['FECHA']).stack([0]))

            gdl_stack = gdl_stack.reset_index().rename(columns={'level_1':'PARAM',
                                                                0:est_dict[s.strip(' ').upper()]})
            
            gdl_stack['FECHA'] = pd.to_datetime(gdl_stack['FECHA'])
            
            gdl_stack = gdl_stack[gdl_stack['FECHA'].dt.year==int(file[6:10])]

            gdl_stack[est_dict[s.strip(' ').upper()]] = pd.to_numeric(gdl_stack[est_dict[s.strip(' ').upper()]], errors='coerce')

            gdl_stack = gdl_stack.groupby(['FECHA','PARAM']).mean()

            all_data = pd.merge(all_data, gdl_stack, how='outer',left_index=True, right_index=True)
            
        
        #print (all_data)
        all_data.to_csv(dir_gdl+'stack/'+file[6:10]+'.csv')



def aqip_mx():

    """Creates two csv files with data from the Air Quality Index Project for mexican cities. 
        The first contains data from the criterion pollutants for the mexican cities in the AQIP database, 
        from January to May from 2017 to 2020.
        The second contains the ammount of dates with data for every city and pollutant and a percentage of
        the total options available.
    """
    
    dir_pcs_aqip = '../data/processed/aqip/'
    
    aqip_mx = pd.read_csv(dir_pcs_aqip+'MX_2015_2020.csv') #Data from AQIP filtered for mexican cities
    
    years = [2017, 2018, 2019, 2020] #Years to be analyzed
    
    aqip_mx['Date'] = pd.to_datetime(aqip_mx['Date'])

    aqip_mx2 = pd.DataFrame()
    
    stat_city = pd.DataFrame(columns=['City','Specie','Count','Pctg','Count_avg','Pctg_avg'])

    for year in years:

        aqip_mx2 = aqip_mx2.append(aqip_mx[aqip_mx['Date'].dt.year==year]) #Dissmisses years not in list

    
    cities = aqip_mx.groupby(['City']).count()
    
    city = cities.index.tolist() #List of cities in the database


    for i in range (5):

        df = pd.DataFrame()

        for year in years:

            df2 = pd.DataFrame()

            y=str(year)
            
            df2['Date'] = pd.date_range(start = pd.Timestamp(y), 
                                           end = pd.Timestamp(y+'-05-31')  ,
                                           freq = 'D')
            df = df.append(df2) #Creates database with months from January to May for the years listed
            

        c_data = aqip_mx2[aqip_mx2['Specie']==pollutant(i)] #Creates a column with the pollutant analyzed

        c_data = c_data.set_index('Date')

        for c in city:

            #Adds the data for every city for the specified pollutant to the DataFrame with all dates
            df=df.merge(c_data[c_data['City']==c]['c_median'], how='left', on='Date').rename(columns={'c_median':c})
            
        
        df = df.set_index('Date')

        #Creates DataFrame to count presence of data by city and pollutant
        res_data = pd.DataFrame(df.stack())
        
        res_data = res_data.reset_index().drop(columns=['Date']).rename(columns={'level_1':'City',
                                                                     0:'Count'}).groupby('City').count()

        res_data['Pctg'] = res_data['Count']/len(df)
            
        df = df.rolling(7, min_periods=1).mean()
        
        #Creates DataFrame to count presence of data by city and pollutant after weekly average
        res_data2 = pd.DataFrame(df.stack())
        res_data2 = res_data2.reset_index().drop(columns=['Date']).rename(columns={'level_1':'City',
                                                             0:'Count_avg'}).groupby('City').count()
        
        res_data2['Pctg_avg'] = res_data2['Count_avg']/len(df)
        res_data = res_data.merge(res_data2, how='outer', on='City')
        
        res_data['Specie'] = pollutant(i)
        
        stat_city = stat_city.append(res_data.reset_index())

        #Saves csv with city data by pollutant    
        df.to_csv(dir_pcs_aqip+'MX_'+pollutant(i)+'_'+str(years[0])+'-'+str(years[len(years)-1])+'.csv')
           
    #Sets multiindex for stat_city
    stat_city = stat_city.set_index(['City','Specie'])
    
    specie = [pollutant(i) for i in range(5)]*15
    
    city2 = city*5
    
    city2.sort()

    index =[city2,specie]

    tuples = list(zip(*index))

    index = pd.MultiIndex.from_tuples(tuples, names=['City','Specie'])
    
    stat_city = stat_city.reindex(index)
    
    #Saves csv with data ammount of dates with data for every city 
    # and pollutant and a percentage of the total options available
    stat_city.to_csv(dir_pcs_aqip+'MX_StatRes_'+str(years[0])+'-'+str(years[len(years)-1])+'.csv')