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
