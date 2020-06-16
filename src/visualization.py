################################################################################
# Module: Station visualizer
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 28/05/2020
################################################################################

import folium
from datosgobmx import client
import pandas as pd
import matplotlib.pyplot as plt

dir_grl = '/home/edgar/Source/Repos/Observatorio-Ciudades/calidad-aire/data/processed/'
dir_fig = '/home/edgar/Source/Repos/Observatorio-Ciudades/calidad-aire/output/figures/cdmx_yearly/'

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

def compare_aq(p, city):

    dir_pcs = '../data/processed/'
    dir_pcs_cat = dir_pcs+'aqip_'+city #Directory to save concatenation
    dir_fig_cmp = '../output/figures/aqip_analysis/'

    compare = pd.read_csv(dir_pcs_cat +city+'_AQIP.csv')
    compare = compare.drop(columns=['count','min','max','median','variance','PARAM','FECHA']).rename(columns={'Specie':'Contaminante',
                                                                                                                'Date':'Fecha'})
    ax = plt.gca()
    compare[compare['Contaminante']==p].plot(kind='scatter', x='Fecha',y='cdmx_median', color='green', ax=ax)
    compare[compare['Contaminante']==p].plot(kind='scatter', x='Fecha',y='aqip_median', color='orange', alpha = 0.75, ax=ax)
    
    plt.ylabel('Concentration: '+p)
    
    plt.savefig(dir_fig_cmp+p+'_x1.png')
    
    #plt.show()

#test

def visualize_stations():
    
    parametros_request = client.makeCall('sinaica-estaciones',{'pageSize':200})

    estaciones = []

    for v in parametros_request['results']:
        aux = pd.DataFrame.from_dict(v,orient='index').T
        estaciones.append(aux)

    estaciones = pd.concat(estaciones, ignore_index=True)
    
    #Quita las estaciones que esten fuera de Mexico
    mask = (estaciones.lat.between(14, 34.5)) & (estaciones.long.between(-120, -70))
    estaciones = estaciones[mask]

    #La variable estaciones son los datos obtenidos de la API, en formato Pandas Dataframe

    centro_lat, centro_lon = 22.396092, -101.731430 #Centro del mapa

    #Creacion del mapa
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=5,
                            tiles = 'cartodb positron')

    #Se colocan los puntos de las estaciones
    for i, row in estaciones.iterrows():

        #Puntos con nombre, latitud y longitud
        popup_text = f"<b> Nombre: </b> {row.nombre} <br> <b> Latitud: </b> {row.lat:.5f} <br> <b> Longitud: </b> {row.long:.5f} <br>"

        #Coloca los marcadores en el mapa
        folium.CircleMarker(location=[row.lat, row.long], radius=5,
                            tooltip = popup_text, fill=True, fill_opacity=0.4).add_to(folium_map)

    return folium_map


def graph_yearly(city):
    """Creates a graph that compares the air quality data for each pollutant from 2017 to 2020

    Args:
        city (str): code for the city to be analysed, for example: cdmx
    """
    years = [2017, 2018, 2019, 2020] #Years to be referenced

    year_dict = {2017:'green', 2018:'blue',
                2019:'orange', 2020:'red'}
    
    
    for i in range(6):
        
        data_mean = pd.read_csv(dir_grl+city+'/'+city+'_2017-2020_filtered_'+pollutant(i)+'.csv').set_index('FECHA')
        
        data_mean['mean'] = data_mean.mean(axis=1)
        
        data_mean = data_mean.reset_index()
        
        data_mean['FECHA'] = pd.to_datetime(data_mean['FECHA'])
    
        
        ax = plt.gca()
        
        for y in years:
            filter_year=data_mean[data_mean['FECHA'].dt.year==y]
            
            filter_year['FECHA'] = filter_year['FECHA'].dt.strftime('%m-%d')
            
            #print(filter_year)
            
            filter_year.plot(kind='scatter', x='FECHA',y='mean', color=year_dict[y], label = str(y), ax=ax)
            
            
        plt.ylabel('Concentration: '+pollutant(i))
        
        plt.savefig(dir_fig+'Year_Compare_'+pollutant(i)+'.png')
        
        ax.clear()

def colors(conc_nrm):
    """Receives a normalized concentration value and returns a hex depending on the air quality level.

    Args:
        conc_nrm (float): result of the division between the averaged concentration and a bad quality concentration.

    Returns:
        str : hex color
    """

    if conc_nrm<=0.25:
        color = '#3CB371'
    elif conc_nrm<=0.5:
        color = '#FFD700'
    elif conc_nrm<=0.75:
        color = '#FF7F50'
    else:
        color = '#483D8B'
        
    return color

def visualize_aqdata_date(city, pollutant, date):
    """ Creates a folium map with stations arranged by size and colour depending on the concentration of the pollutant.

    Args:
        city (str): code for the city to be analysed, for example: cdmx
        pollutant (str): pollutant to be plotted
        date (str): date to be analysed

    Returns:
        folium map
    """
    city_stations = pd.read_csv('../data/raw/Grl/stations/city_stations.csv')

    city_dict = {'cdmx':'Valle de México'}
    
    p_limits = {'PM10':214, 'O3':154, 'CO':16.5,
               'PM25':97.4, 'SO2':195,'NO2':315}
    
    data_bydateParam = pd.read_csv(dir_grl+'processed/'+city+'/'+city+'_2017-2020_filtered_'+pollutant+'.csv').set_index('FECHA')
    
    centro_lat, centro_lon = 19.442810, -99.131233 #Centro del mapa

    #Creacion del mapa
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=10,
                            tiles = 'cartodb positron')

    for i, est in city_stations[city_stations['city']==city_dict[city]].iterrows():

        est_code = city_stations.loc[(i),'codigo']

        #Coloca los marcadores en el mapa
        c_value = data_bydateParam.loc[(date),est_code]
        c_graph = (data_bydateParam.loc[(date),est_code])/p_limits[pollutant]

        #Puntos con nombre, latitud y longitud
        popup_text = f"<b> Nombre: </b> {est.nombre} <br> <b> Latitud: </b> {est.lat:.5f} <br> <b> Longitud: </b> {est.long:.5f} <br> <b> Contaminante: </b> {pollutant} <br> <b> Conc: </b> {c_value} <br>"

        #Coloca los marcadores en el mapa
        folium.CircleMarker(location=[est.lat, est.long], radius=c_graph*50,
                            tooltip = popup_text, fill=True, color=colors(c_graph),
                            fill_opacity=0.65).add_to(folium_map)

    return(folium_map)

def clr_change(conc_cmp):
    """Function that receives a float of a normalyzed concentration and returns a hex.

    Args:
        conc_cmp (float): value resulted from the division bewteen the concentration of the year analysed and the year prior.

    Returns:
        str: hex with the code, if the value of the current year is smaller it's blue, otherwise it's red.
    """
    
    if conc_cmp>=0:
        color = '#F84A50'
    else:
        color = '#6086CA'
        
    return color

def compare_year_prior(city, pollutant, date):
    """Creates a map with the analysis of the average between the input date and the previous year for a selected pollutant.

    Args:
        city (str): code for the city to be analysed, for example: cdmx
        pollutant (str): pollutant to be plotted
        date (str): date to be analysed

    Returns:
        folium map where a blue marker indicates a smaller value of the input date concentration and, the bigger the marker the larger the concentration
    """
    city_stations = pd.read_csv('../data/raw/Grl/stations/city_stations.csv')

    city_dict = {'cdmx':'Valle de México'}
    
    prev_year = str(int(date[:4])-1)+date[4:]
    
    data_bydateParam = pd.read_csv(dir_grl+'processed/'+city+'/'+city+'_2017-2020_filtered_'+pollutant+'.csv').set_index('FECHA')
    
    centro_lat, centro_lon = 19.442810, -99.131233 #Centro del mapa

    #Creacion del mapa
    folium_map = folium.Map(location=[centro_lat,centro_lon], zoom_start=10,
                            tiles = 'cartodb positron')

    for i, est in city_stations[city_stations['city']==city_dict[city]].iterrows():

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