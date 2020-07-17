################################################################################
# Module: Data gathering and treatment
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 17/07/2020
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
import src


def parse_mediciones_json(json_file):
    """Function that converts json files to csv, function from: https://datos.gob.mx/blog/ventilando-datos-abiertos-sobre-calidad-del-aire

    Args:
        json_file {json} -- file in json

    Returns:
        csv -- json convedescriptionrted to csv
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


def data_sinaica(city, num_datos):
    """Function that downloads csv with from SINAICA for a given city

    Args:
        city {str} -- code for city to be downloaded

    Return
        csv  -- csv with air quality data for the specified city from the SINAICA database

    """
    dir_raw = '../data/raw/' #dictionary for raw data

    #checks if directory exists and creates it if it doesn't
    if not os.path.isdir(dir_raw+city): 
        os.mkdir(dir_raw+city) 
        for i in range(5): os.mkdir(dir_raw+city+'/'+src.pollutant(i))


    #calls pollutant functions and gathers data for the specified city and pollutant
    for i in range(5):
        filename = city+'_'+src.pollutant(i)
        filename = dir_raw+city+'/'+src.pollutant(i)+'/'+filename
        
        #calls datosgobmx and gets data in json
        data_api = client.makeCall('sinaica',{'pageSize':num_datos, 'city':src.city_name(city), 'parametro':src.pollutant(i)})
            
        with open (filename,'w') as outfile:
            json.dump(data_api,outfile)
            
        sinaica_mediciones = parse_mediciones_json(filename)

        sinaica_mediciones.to_csv(filename+'.csv', index=False) #writes csv file from json

def stations_csv():
    """Function that downloads csv with information for all Mexican air quality stations using SINAICA api

    Returns:
        csv -- csv with information for all air quality stations from the SINAICA database

    """
        
    parametros_request = client.makeCall('sinaica-estaciones',{'pageSize':200}) #calls datosgobmx function and gathers data
    dir_raw_grl = '../data/raw/Grl/'

    stations = [] #list which saves station information

    #gathers data from all stations and interates over them
    for v in parametros_request['results']:
        aux = pd.DataFrame.from_dict(v,orient='index').T
        stations.append(aux)

    stations = pd.concat(stations, ignore_index=True)

    #Removes stations that are out of Mexico
    mask = (stations.lat.between(14, 34.5)) & (stations.long.between(-120, -70))
    stations = stations[mask]

    filename = dir_raw_grl+'estaciones'

    stations.to_csv (r''+filename+'.csv', index = False, header=True) #saves to csv


def merge_aq(city, year_limit=2020):
    """Function that merges the databases from air quality stations for a given city 
        into a single csv from a period starting at 2017 and ending at year_limit, set to default at 2020

    Args:
        city {str} -- string containing city code to be analyzed
        year_limit {int} -- int with limit year to be analyzed, set to 2020 by default

    Returns:
        csv -- csv with all the data from air quality stations
    """

    dir_raw = '../data/raw/'
    dir_pcs = '../data/processed/'
    
    all_data = pd.DataFrame() #DataFrame that will contain all data

    for year in range(2017,year_limit+1):
        
        #for i in range(5):
            #for statement used in cdmx   
            #data = pd.read_excel(dir_raw+city+str(year)[-2:]+'RAMA\\'+str(year)+strc.pollutant(i)+'.xls').replace(-99,np.NaN)
        
        #access air quality data for a specified year
        data = pd.read_csv(dir_raw+city+'/stack/'+str(year)+'.csv').replace(r'^\s*$',np.nan,regex=True)
        data = data.set_index(['PARAM','FECHA'])
        all_data = all_data.append(data)
    
    filename = dir_pcs + city + '/' + city + '_' + str(2017)+'-'+str(year_limit)

    all_data.to_csv (r''+filename+'.csv', index = True, header=True) #saves DataFrame to csv

def res_aqdata(city, year_limit=2020):
    """Function that groups data from air quality stations by date and parameter for every station from 
        a period starting at 2017 and ending at year_limit, set to default at 2020

    Args:
        city {str} -- string containing city code to be analyzed
        year_limit {int} -- int with limit year to be analyzed, set to 2020 by default

    Returns:
        csv -- csv with sumarized data
    """

    dir_pcs = '../data/processed/' #directory for processed data

    res_data = pd.read_csv(dir_pcs +city + str(2017)+'-'+str(year_limit)+'.csv', index_col = [0,1]) 

    res_data = res_data.groupby(['PARAM','FECHA']).mean() #calculates mean for pollutant and date
    
    filename = dir_pcs +'res_'+ str(2017)+'-'+str(year_limit)

    res_data.to_csv (r''+filename+'.csv', index = True, header=True) #saves csv
    
    
def aq_daily_median(city, year_limit=2020):
    """Function that calculates the median by day for a given city and pollutant from 
        a period starting at 2017 and ending at year_limit, set to default at 2020

    Args:
        city {str} -- city code to calculate median
        year_limit {int} -- int with limit year to be analyzed, set to 2020 by default

    Returns:
        csv -- csv for the date and calculated median
    """

    dir_pcs = '../data/proccessed/'

    aq_median_data = pd.read_csv(dir_pcs +city+'res_'+ str(2017)+'-'+str(year_limit)+'.csv', index_col = [0,1]).median(axis=1)
    
    aq_median_data.to_csv(dir_pcs+city+'median_res_'+ str(2017)+'-'+str(year_limit)+'.csv')


def aqip_data():
    """Function that extracts data for mexican city from the Air Quality Index Project database.

    Returns:
        csv -- csv with AQIP data for mexican cities

    """
    dir_raw_aqip = '../data/raw/AirQualityIndexProject/world_data/'
    dir_pcs_aqip = '../data/processed/aqip/'
    
    all_data = pd.DataFrame()

   #reads all csv files from specified directory 
    for file in os.listdir(dir_raw_aqip):

        filename = dir_raw_aqip + file
        
        data_aqip = pd.DataFrame()
        
        data_aqip = pd.read_csv(filename, skiprows=4)
        
        data_aqip['Specie'] = data_aqip['Specie'].str.upper() #changes pollutants to capital letters
        
        data_aqip = data_aqip.set_index(['Specie'])
        
        data_aqip = data_aqip[data_aqip['Country']=='MX'].drop(['Country'], axis=1) #filters for Mexico
        
        all_data = all_data.append(data_aqip)
        
    #Condition that selects pollutant
    cond = [all_data.index == 'O3', all_data.index == 'CO', all_data.index == 'PM10', 
           all_data.index == 'PM25', all_data.index == 'NO2', all_data.index == 'SO2']
    
    #Choice that dictates what happends for each case
    choice = [all_data['median'].apply(src.o3_conc), all_data['median'].apply(src.co_conc), 
             all_data['median'].apply(src.pm10_conc), all_data['median'].apply(src.pm25_conc),
             all_data['median'].apply(src.no2_conc), all_data['median'].apply(src.so2_conc)]
    
    #Calculates a new column with the data converted from 
    #air quality index to concentration by pollutant

    all_data['c_median'] = np.select(cond, choice)
    
    all_data = all_data.reset_index().set_index(['City','Specie','Date'])

    all_data.to_csv(dir_pcs_aqip +'MX_2015_2020.csv')
    
    
def gdl_data ():
    """Function that merges and adjusts format for SIMAJ database for Guadalajara's stations

    Returns:
        csv -- 
    
    """

    dir_gdl = '../data/raw/gdl/'
    
    #dictionary for stations codes and names
    est_dict = {'ÁGUILAS':'AGU', 'ATEMAJAC':'ATM', 'CENTRO':'CEN', 
                'LAS PINTAS':'PIN', 'LOMA DORADA':'LDO', 'MIRAVALLE':'MIR', 'OBLATOS':'OBL', 
                'SANTA FE':'SFE', 'TLAQUEPAQUE':'TLA', 'VALLARTA':'VAL'} 
    
    #check for file or directory in dir_gdl
    for file in os.listdir(dir_gdl):

        f_check = os.path.join(dir_gdl,file)

        if os.path.isfile(f_check):
            #SIMAJ data is in xls and in different sheets
            xls = xlrd.open_workbook(r''+dir_gdl+file, on_demand=True)
            sheets = xls.sheet_names() #creates list form sheet names

        else:
            continue
        
        year = file[6:10] #gathers the year from the file name

        #creates DataFrame to save pollutant information
        df = pd.DataFrame(columns=['O3','CO','PM10','SO2','NO2'])

        #adds a date column and creates daily information
        df['FECHA'] = pd.date_range(start = pd.Timestamp(year), 
                                   end = pd.Timestamp(year) + pd.tseries.offsets.YearEnd(0),
                                   freq = 'D')

        df = df.set_index('FECHA')
        df = df.stack(dropna=False) #stacks DataFrame so for every date there are 5 rows with criterion pollutants
        all_data = pd.DataFrame(df) #passes inforation to new DataFrame
        all_data = all_data.rename_axis(index=['FECHA','PARAM']) #sets dates and pollutants as index
        all_data = all_data.drop(columns=[0]) #removes empty column
        

        for s in sheets:
            
            #reads excel with data and sets empty cells as nan
            gdl_data = pd.read_excel(dir_gdl+file, sheet_name = s).rename(columns={'Fecha':'FECHA',
                                                                                   'Hora':'HORA'}).replace(r'^\s*$', 
                                                                                                           np.nan, 
                                                                                                           regex=True)
            gdl_data.columns = [col.strip() for col in gdl_data.columns] #removes spaces from columns
            
            gdl_data = gdl_data[['FECHA','O3','NO2','SO2','PM10','CO']] #filters data

            gdl_data['FECHA'] = gdl_data['FECHA'].dt.date

            #stacks gdl DataFrame so for every date there are 5 rows with criterion pollutants
            gdl_stack = pd.DataFrame(gdl_data.set_index(['FECHA']).stack([0]))

            #changes name from stacked column with concentration information
            gdl_stack = gdl_stack.reset_index().rename(columns={'level_1':'PARAM',
                                                                0:est_dict[s.strip(' ').upper()]})
            
            gdl_stack['FECHA'] = pd.to_datetime(gdl_stack['FECHA'])
            
            #because the data base contains dates out from the analyzed year the DataFrame is filtered
            gdl_stack = gdl_stack[gdl_stack['FECHA'].dt.year==int(file[6:10])]

            #removes sapces from sheet names and sets columns as numbers avoiding spaces
            gdl_stack[est_dict[s.strip(' ').upper()]] = pd.to_numeric(gdl_stack[est_dict[s.strip(' ').upper()]], errors='coerce')

            gdl_stack = gdl_stack.groupby(['FECHA','PARAM']).mean()

            #adds data from gdl_stack for a specified year to all_data which 
            #will contain information for every year
            all_data = pd.merge(all_data, gdl_stack, how='outer',left_index=True, right_index=True)
            
        
        all_data.to_csv(dir_gdl+'stack/'+file[6:10]+'.csv') #saves data for all years, stations and parameters



def aqip_mx(month_limit=5, year_limit=2020):

    """Creates two csv files with data from the Air Quality Index Project for mexican cities. 
        The first contains data from the criterion pollutants for the mexican cities in the AQIP database, 
        from January to month_limit, set by default to May, from 2017 to year_limit, set by default to 2020
        The second contains the ammount of dates with data for every city and pollutant and a percentage of
        the total options available

    Args:
        year_limit{int} -- int with limit year to be analyzed, set to 2020 by default
        month_limit {int} -- int with limit month to be analyzed, set to 5 (May) by default

    Returns:
        csv -- data from the criterion pollutants for the mexican cities in the AQIP database
        csv -- ammount of dates with data for every city and pollutant and a percentage of the total options available
    """
    
    dir_pcs_aqip = '../data/processed/aqip/'
    
    aqip_mx = pd.read_csv(dir_pcs_aqip+'MX_2015_'+str(year_limit)+'.csv') #Data from AQIP filtered for mexican cities
    
    aqip_mx['Date'] = pd.to_datetime(aqip_mx['Date'])

    aqip_mx2 = pd.DataFrame()
    
    stat_city = pd.DataFrame(columns=['City','Specie','Count','Pctg','Count_avg','Pctg_avg'])

    for year in range(2017,year_limit+1):

        aqip_mx2 = aqip_mx2.append(aqip_mx[aqip_mx['Date'].dt.year==year]) #Dissmisses years not in range

    
    cities = aqip_mx.groupby(['City']).count()
    
    city = cities.index.tolist() #List of cities in the database


    for i in range (5):

        df = pd.DataFrame()

        for year in range(2017,year_limit+1):

            df2 = pd.DataFrame()

            y=str(year)
            
            month = str(month_limit) #adds month to string
             
            if month_limit<10:
                month = '0'+str(month_limit) #if month is smaller than 10 it adds a zero

            #specifies day depending on month
            if month == '2':
                day = '29'
            
            elif month in {1, 3, 5, 7, 8, 10, 12}:
                day = '31'

            else:
                day = '30'


            df2['Date'] = pd.date_range(start = pd.Timestamp(y), 
                                           end = pd.Timestamp(y+'-'+month+'-'+day)  ,
                                           freq = 'D')
            df = df.append(df2) #Creates database with days from January to month_limit for the years in range
            

        c_data = aqip_mx2[aqip_mx2['Specie']==src.pollutant(i)] #Creates a column with the pollutant analyzed

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
        
        res_data['Specie'] = src.pollutant(i)
        
        stat_city = stat_city.append(res_data.reset_index())

        #Saves csv with city data by pollutant    
        df.to_csv(dir_pcs_aqip+'MX_'+src.pollutant(i)+'_'+str(2017)+'-'+str(year_limit)+'.csv')
           
    #Sets multiindex for stat_city
    stat_city = stat_city.set_index(['City','Specie'])
    
    specie = [src.pollutant(i) for i in range(5)]*15
    
    city2 = city*5
    
    city2.sort()

    index =[city2,specie]

    tuples = list(zip(*index))

    index = pd.MultiIndex.from_tuples(tuples, names=['City','Specie'])
    
    stat_city = stat_city.reindex(index)
    
    #Saves csv with data ammount of dates with data for every city 
    # and pollutant and a percentage of the total options available
    stat_city.to_csv(dir_pcs_aqip+'MX_StatRes_'+str(2017)+'-'+str(year_limit)+'.csv')