################################################################################
# Module: Station visualizer
# developed by: Edgar Egurrola
# 			  edgar.egurrola@tec.mx
# updated: 28/05/2020
################################################################################

import folium
from datosgobmx import client
import panda as pd

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