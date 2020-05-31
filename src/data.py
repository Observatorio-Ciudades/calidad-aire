#Codigo para descargar los datos de calidad del aire de guadalajara y guardarlos en un csv
#Observatorio de ciudades

from pathlib import Path
import json
import os
from datosgobmx import client

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

#Descarga datos de la ciudad, contaminantes y cantidad de datos establecidos
ciudad = 'Guadalajara'
contaminante = ['O3', 'PM10', 'CO']
num_datos = 10000

#Direccion para guardar los csv
direccion = 'D:\\Users\\edgar\\Source\\Repos\\Observatorio-Ciudades\\calidad-aire\\data\\raw\\'

#Checa si existe la carpeta de la ciudad y contaminantes y los crea si no existen
if not os.path.isdir(direccion+ciudad): 
    os.mkdir(direccion+ciudad) 
    for c in contaminante: os.mkdir(direccion+ciudad+'\\'+c)

#Itera sobre la lista de contaminantes y obtiene ese parametro para la ciudad establecida
for p in contaminante:
    filename = ciudad+'_'+p
    filename = direccion+ciudad+'\\'+p+'\\'+filename
    
    data_api = client.makeCall('sinaica',{'pageSize':num_datos, 'city':ciudad, 'parametro':p})
        
    with open (filename,'w') as outfile:
        json.dump(data_api,outfile)
        
    sinaica_mediciones = parse_mediciones_json(filename)
    sinaica_mediciones.to_csv(filename+'.csv', index=False)

def est_csv():
    """Downloads csv with information about Mexican air quality stations

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
    
    direccion = 'D:\\Users\\edgar\\Source\\Repos\\Observatorio-Ciudades\\calidad-aire\\data\\raw\\Grl\\'

    filename = direccion+'estaciones'

    estaciones.to_csv (r''+filename+'.csv', index = False, header=True)