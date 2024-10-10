import pika
import random
import time
import requests
from geolib import geohash

topics_veicolo = { 'posizione' : 'veicolo.posizione', 
            'velocità' : 'veicolo.velocità'  }
topics_bs = { 'posizione' : 'bs.posizione', 
          'traffico' : 'bs.traffico',
            'segnale' : 'bs.signal'  }

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
            longitudine = cella ["lon"]

            # Stampa il cellid e le coordinate della cella scelta
           
        else:
            print("Nessuna cella trovata nell'area specificata.")

else:
        # Gestione di errori in caso di risposta non corretta
        print(f"Errore: {response.status_code}")
        print("Dettagli:", response.text)
base_station_id = f"bs {cellid}"
position_bs = geohash.encode (latitudine,longitudine,7)

time.sleep(5)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host= broker))
channel = connection.channel()

channel.exchange_declare(exchange= 'topic', exchange_type="topic")
timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
traffic = {"tmstp" : timestamp, "e": [{ "n" : "3432/0/1" , "v" : f"{random.choice("low", "high")}" }] } # 0 low 1 medium 2 high
signal = {"tmstp" : timestamp, "e": [ { "n" : "4/0/2" , "v" : f"{random.randint(-120, -50)} " }] } 

channel.basic_publish(exchange='topic', routing_key = topics_bs["posizione"], body=position_bs)
print (f"Messaggio {position_bs} inviato!")
channel.basic_publish(exchange='topic', routing_key = topics_bs["traffico"], body=traffic)
print (f"Messaggio {traffic} inviato!")
channel.basic_publish(exchange='topic', routing_key = topics_bs["segnale"], body=signal)
print (f"Messaggio {signal} inviato!")

connection.close()

"""
def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
        for topic in topics_veicolo.values():
         client.subscribe(topic)
         print(f"Mi sono sottoscritto al topic {topic}")
        
    else:
        print(f"Failed to connect, return code {reason_code}")

def on_message(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")

def publish(client):
    # Generazione dinamica dei valori dei messaggi
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    traffic = {"tmstp" : timestamp, "e": [{ "n" : "3432/0/1" , "v" : f"{random.randint(0, 2)}" }] } # 0 low 1 medium 2 high
    signal = {"tmstp" : timestamp, "e": [ { "n" : "4/0/2" , "v" : f"{random.randint(-120, -50)} " }] } 
    messages = {
        topics_bs['posizione']: f"Posizione: {position_bs}",  # Valore dinamico
        topics_bs['traffico']: f"Traffico: {traffic} veicoli",  # Valore dinamico
        topics_bs['segnale']: f"Segnale: {signal} dBm"  # Valore dinamico
    }
    
    for topic, message in messages.items():
        result = client.publish(topic, message)
        # Controllo se il messaggio è stato pubblicato con successo
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            print(f"Messaggio '{message}' inviato al topic '{topic}'")
        else:
            print(f"Errore nell'invio del messaggio al topic '{topic}'. Codice errore: {result.rc}")

def run():
    bs = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, base_station_id)
    time.sleep(5)
    bs.on_connect = on_connect
    bs.on_message = on_message  # Associa il callback on_message
    bs.connect(broker, port,5)
    
    
    bs.loop_start()
    try:
        while True:
            publish(bs)
            time.sleep(10)
    except KeyboardInterrupt:
        bs.loop_stop()
        bs.disconnect()


if __name__ == '__main__':
    
      run()

"""