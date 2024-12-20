import pika
import random
import time
import requests
from geolib import geohash
import xml.etree.ElementTree as ET
import traci.exceptions

api = "pk.3f5c5de68b06b081a2e814e3b186f773"
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

    print(f"Min Latitudine: {min_latitude}, Min Longitudine: {min_longitude}")
    print(f"Max Latitudine: {max_latitude}, Max Longitudine: {max_longitude}")
else:
    print("La bounding box non è presente nel file OSM.")

URL = f"http://www.opencellid.org/cell/getInArea?key={api}&BBOX={min_latitude},{min_longitude},{max_latitude},{max_longitude}&format=json"
broker = "amqp-broker"
port = 5672

# Effettua la richiesta
response = requests.get(URL)

if response.status_code == 200:
    messaggio_json = response.json()
    cell_data_array = []
    
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

    if cell_data_array:
        cella = random.choice(cell_data_array)
        cellid = cella["cellid"]
        latitudine = cella["lat"]
        longitudine = cella["lon"]

        print(f"Cell ID: {cellid}, Lat: {latitudine}, Lon: {longitudine}")
    else:
        print("Nessuna cella trovata nell'area specificata.")
else:
    print(f"Errore: {response.status_code}")
    print("Dettagli:", response.text)

# Genera i dati della stazione base
base_station_id = f"{cellid}"
geohash = geohash.encode(latitudine, longitudine, 6)

topics_veicolo = {
    'latitudine': f'{geohash}.vehicle.*.3430.0.',
                  'longitudine': f'{geohash}.vehicle.*.3430.0.',
                  'velocità': f'{geohash}.vehicle.*.3430.0.',
                  'emissioni': f'{geohash}.vehicle.*.3428.0.',
                  }
topics_bs = {
     'latitudine' : f'{geohash}.bs.{base_station_id}.3430.0.',
     'longitudine' : f'{geohash}.bs.{base_station_id}.3430.0.', 
     'traffico': f'{geohash}.bs.{base_station_id}.3432.0.',
     'emissioni' : f'{geohash}.bs.{base_station_id}.3428.0.'}  


def on_message(channel, method_frame, header_frame, body):
    print(f"Ricevuto il messaggio con body {body.decode()} dal topic {method_frame.routing_key}")

time.sleep(5)

credentials = pika.PlainCredentials("guest", 'guest')
connection_params = pika.ConnectionParameters(host=broker, port=port, credentials=credentials)
time.sleep(5)
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()

# Dichiarazione e sottoscrizione ai topic
channel.exchange_declare(exchange='topic', exchange_type='topic')
for topic_name, topic_key in topics_veicolo.items():
    queue = channel.queue_declare(queue=topic_name, exclusive=True).method.queue
    channel.queue_bind(exchange='topic', queue=queue, routing_key=topic_key)
    channel.basic_consume(queue=queue, on_message_callback=on_message, auto_ack=True)
    print(f"Sottoscritto al topic {topic_key}")

try:
    while True:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        latitude_msg = {
            "tmstp": timestamp, 
            "e": [{"n": "1", "v": str(latitudine)}]
        }
        longitude_msg = {
            "tmstp": timestamp, 
            "e": [{"n": "2", "v": str(longitudine)}]
        }
        traffic = random.randint (40,50)
        traffic_message = {"tmstp" : timestamp ,"e": [{"n" : "1" , "v" : f"{traffic} " }] } 
        emission = 10000*traffic
        emission_message = {"tmstp" : timestamp ,"e": [{"n" : "17" , "v" : f"{emission} " }] }
        
        messages = (
            (topics_bs['latitudine'], latitude_msg),
            (topics_bs['longitudine'], longitude_msg),
            (topics_bs['traffico'], f"{traffic_message}"),
            (topics_bs['emissioni'], f"{emission_message}")   # Valore dinamico
            
        )

        # Pubblicazione dei messaggi
        for topic, message in messages:
            channel.basic_publish(exchange='topic', routing_key=topic, body=str(message))
            print(f"Messaggio inviato al topic {topic}: {message}")
        
        time.sleep(10)
        channel.connection.process_data_events()
except KeyboardInterrupt:
    print("Interruzione manuale del programma.")
finally:
    connection.close()
