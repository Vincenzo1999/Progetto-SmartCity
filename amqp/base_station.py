import pika
import random
import time
import requests
from geolib import geohash

topics_veicolo = { 'posizione': 'veicolo.posizione', 
                   'velocità': 'veicolo.velocità' }
topics_bs = { 'posizione': 'bs.posizione', 
              'traffico': 'bs.traffico',
              'segnale': 'bs.signal' }

api = "pk.3f5c5de68b06b081a2e814e3b186f773"
latitudine_max = 38.1194325
latitudine_min = 38.109894
longitudine_max = 15.6574058
longitudine_min = 15.6439948
URL = f"http://www.opencellid.org/cell/getInArea?key={api}&BBOX={latitudine_min},{longitudine_min},{latitudine_max},{longitudine_max}&format=json"

broker = "amqp-broker"
port = 5672

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

        # Stampa il cellid e le coordinate della cella scelta
        print(f"Cell ID: {cellid}, Lat: {latitudine}, Lon: {longitudine}")
    else:
        print("Nessuna cella trovata nell'area specificata.")
else:
    # Gestione di errori in caso di risposta non corretta
    print(f"Errore: {response.status_code}")
    print("Dettagli:", response.text)

# Genera i dati della stazione base
base_station_id = f"bs {cellid}"
position_bs = geohash.encode(latitudine, longitudine, 7)

time.sleep(5)

# Imposta i parametri di connessione con RabbitMQ
connection_params = pika.ConnectionParameters(host=broker, port=port)
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()

# Dichiarare un exchange di tipo topic
channel.exchange_declare(exchange='topic', exchange_type='topic')

# Genera un timestamp
timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# Messaggi da pubblicare
traffic = {
    "tmstp": timestamp, 
    "e": [{ "n": "3432/0/1", "v": random.choice(["low","medium","high"]) }]
}

signal = {
    "tmstp": timestamp, 
    "e": [{ "n": "4/0/2", "v": str(random.randint(-120, -50)) }]
}

# Pubblicare i messaggi
channel.basic_publish(exchange='topic', routing_key=topics_bs["posizione"], body=position_bs)
print(f"Messaggio {position_bs} inviato!")

channel.basic_publish(exchange='topic', routing_key=topics_bs["traffico"], body=str(traffic))
print(f"Messaggio {traffic} inviato!")

channel.basic_publish(exchange='topic', routing_key=topics_bs["segnale"], body=str(signal))
print(f"Messaggio {signal} inviato!")

# Chiudere la connessione
connection.close()
