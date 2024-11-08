from paho.mqtt import client as mqtt_client
import random
import time
import requests
from geolib import geohash
import xml.etree.ElementTree as ET
import json

api = "pk.3f5c5de68b06b081a2e814e3b186f773"

# Percorso del file .osm
osm_file_path = "/app/Stadio.osm"

# Carica il file XML
tree = ET.parse(osm_file_path)
root = tree.getroot()

# Estrai la bounding box dall'elemento 'bounds'
bounds = root.find('bounds')
if bounds is not None:
    min_latitude = float(bounds.attrib['minlat'])
    min_longitude = float(bounds.attrib['minlon'])
    max_latitude = float(bounds.attrib['maxlat'])
    max_longitude = float(bounds.attrib['maxlon'])

    # Stampa i risultati
    print(f"Min Latitudine: {min_latitude}, Min Longitudine: {min_longitude}")
    print(f"Max Latitudine: {max_latitude}, Max Longitudine: {max_longitude}")
else:
    print("La bounding box non è presente nel file OSM.")
URL = f"http://www.opencellid.org/cell/getInArea?key={api}&BBOX={min_latitude},{min_longitude},{max_latitude},{max_longitude}&format=json"

broker = "mqtt-broker"
port = 1883

# Effettua la richiesta
response = requests.get(URL)

# Controlla se la richiesta è andata a buon fine
if response.status_code == 200:
    # Converti la risposta in formato JSON
    messaggio_json = response.json()

    # Inizializza un array per memorizzare i dati delle celle
    cell_data_array = []

    # Estrai e memorizza 'cellid' e le coordinate in un array
    for cell in messaggio_json.get("cells", []):
        cellid = cell.get("cellid")
        lat = cell.get("lat")
        lon = cell.get("lon")

        if cellid is not None and lat is not None and lon is not None:
            cell_data_array.append({
                "cellid": cellid,
                "lat": lat, 
                "lon": lon
            })

    # Se ci sono celle disponibili, scegli una cella casuale e stampa le informazioni
    if cell_data_array:
        cella = random.choice(cell_data_array)  # Seleziona una cella casuale
        cellid = cella["cellid"]
        latitudine = cella["lat"]
        longitudine = cella["lon"]

else:
    # Gestione di errori in caso di risposta non corretta
    print(f"Errore: {response.status_code}")
    print("Dettagli:", response.text)
    
base_station_id = f"{cellid}"
geohash_value = geohash.encode(latitudine, longitudine, 6)

topics_veicolo = {
    'latitudine': f'{geohash_value}/vehicle/+/3430/0/',
    'longitudine': f'{geohash_value}/vehicle/+/3430/0/',
    'velocità': f'{geohash_value}/vehicle/+/3430/0/',
    'emissioni': f'{geohash_value}/vehicle/+/3428/0/',
}
topics_bs = {
    'latitudine': f'{geohash_value}/bs/{base_station_id}/3430/0/',
    'longitudine': f'{geohash_value}/bs/{base_station_id}/3430/0/', 
    'traffico': f'{geohash_value}/bs/{base_station_id}/3432/0/',
    'emissioni': f'{geohash_value}/bs/{base_station_id}/3428/0/',
}  

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
        for topic in topics_veicolo.values():
            client.subscribe(topic)
            print(f"Mi sono sottoscritto al topic {topic}")
    else:
        print(f"Failed to connect, return code {reason_code}")

def on_message(client, userdata, message):
    print(f"Received message {message.topic} {message.payload.decode()}")

def publish(client):
    # Generazione dinamica dei valori dei messaggi
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    longitudine_antenna = {"tmstp": timestamp, "e": [{"n": "2", "v": f"{longitudine}"}]}
    latitudine_antenna = {"tmstp": timestamp, "e": [{"n": "1", "v": f"{latitudine}"}]}
    traffic = random.randint(40, 50)
    traffic_message = {"tmstp": timestamp, "e": [{"n": "1", "v": f"{traffic}"}]} 
    emission = 10000 * traffic
    emission_message = {"tmstp": timestamp, "e": [{"n": "17", "v": f"{emission}"}]}
     
    messages = [
        (topics_bs['latitudine'], json.dumps(latitudine_antenna)),
        (topics_bs['longitudine'], json.dumps(longitudine_antenna)),  # Valore dinamico
        (topics_bs['traffico'], json.dumps(traffic_message)),
        (topics_bs['emissioni'], json.dumps(emission_message))   # Valore dinamico
    ]
    
    for topic, message in messages:
        result = client.publish(topic, message)
        # Controllo se il messaggio è stato pubblicato con successo
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            print(f"Messaggio {topic} {message} inviato")
        else:
            print(f"Errore nell'invio del messaggio al topic '{topic}'. Codice errore: {result.rc}")

def run():
    bs = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, base_station_id)
    time.sleep(5)
    bs.on_connect = on_connect
    bs.on_message = on_message  # Associa il callback on_message
    bs.connect(broker, port, 5)
    
    bs.loop_start()
    try:
        while True:
            publish(bs)
            time.sleep(15)
    except KeyboardInterrupt:
        bs.loop_stop()
        bs.disconnect()

if __name__ == '__main__':
    run()
