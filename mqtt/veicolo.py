import random
import time
from paho.mqtt import client as mqtt_client
from geolib import geohash
import xml.etree.ElementTree as ET
import traci
import sumolib
import traci.exceptions

# Configurazione del broker MQTT
broker = "mqtt-broker"
port = 1883

# Percorso del file .osm
osm_file_path = "/app/Stadio.osm"

# Carica il file XML e trova la bounding box
tree = ET.parse(osm_file_path)
root = tree.getroot()
bounds = root.find('bounds')
if bounds is not None:
    min_latitude = float(bounds.attrib['minlat'])
    min_longitude = float(bounds.attrib['minlon'])
    max_latitude = float(bounds.attrib['maxlat'])
    max_longitude = float(bounds.attrib['maxlon'])
else:
    print("La bounding box non è presente nel file OSM.")

# Funzione di connessione MQTT
def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print("Connesso al broker MQTT!")
    else:
        print(f"Connessione fallita, codice di ritorno {reason_code}")

# Funzione per ricevere messaggi
def on_message(client, userdata, message):
    print(f"Messaggio  '{message.topic}''{message.payload.decode()}' ricevuto ")

# Funzione per pubblicare messaggi
def publish_messages(client, messages):
    for topic, message in messages.items():
        result = client.publish(topic, message)
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            print(f"Messaggio '{topic}''{message}' inviato ")
            time.sleep(0.5)
        else:
            print(f"Errore nell'invio del messaggio al topic '{topic}'. Codice errore: {result.rc}")

# Funzione principale di esecuzione
def run():
    veicolo_id = "56"
    veicolo = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, veicolo_id)
    
    veicolo.on_connect = on_connect
    veicolo.on_message = on_message
    veicolo.connect(broker, port, 5)
    veicolo.loop_start()
    
    try:
        path = "/app/Stadio.sumocfg"
        traci.start(["sumo", "-c", path, "--step-length", "1"])

        vehicle_routes = {}
        for vehicle in sumolib.xml.parse("/app/Stadio.rou.xml", "vehicle"):
            route = vehicle.route[0]
            edges = route.edges.split()
            vehicle_routes[vehicle.id] = edges

        active_vehicles = set()
        previous_geohash = None
        step = 0

        while step < 2000:  # Aumenta il limite della simulazione se necessario
            traci.simulationStep()
            new_vehicles = traci.simulation.getDepartedIDList()
            active_vehicles.update(new_vehicles)

            messages = {}

            if veicolo_id in list(active_vehicles):
                try:
                    x, y = traci.vehicle.getPosition(veicolo_id)
                    lon, lat = traci.simulation.convertGeo(x, y)
                    
                    geohash_value = geohash.encode(lat, lon, 6)

                    # Controllo e aggiornamento della sottoscrizione in base al geohash
                    if geohash_value != previous_geohash:
                        # Disiscrivi dal topic del geohash precedente, se esistente
                        if previous_geohash:
                            old_topics = {
                                'posizione': f'{previous_geohash}/{veicolo_id}/3430/0/',
                                'traffico': f'{previous_geohash}/{veicolo_id}/3432/0/'
                            }
                            for topic in old_topics.values():
                                veicolo.unsubscribe(topic)
                                print(f"Disiscritto dal topic {topic}")

                        # Aggiorna e sottoscrivi ai topic relativi al nuovo geohash
                        topics_bs = {
                            'posizione': f'{geohash_value}/+/3430/0/',
                            'traffico': f'{geohash_value}/+/3432/0/',
                            'signal': f'{geohash_value}/+/4/0/'
                        }
                        for topic in topics_bs.values():
                            veicolo.subscribe(topic)
                            print(f"Sottoscritto al topic {topic}")

                        previous_geohash = geohash_value  # Aggiorna il geohash precedente
                    topics_veicolo = {'latitudine': f'{geohash_value}/{veicolo_id}/3430/0/',
                  'longitudine': f'{geohash_value}/{veicolo_id}/3430/0/',
                  'velocità': f'{geohash_value}/{veicolo_id}/3430/0/',
                  'traffico': f'{geohash_value}/{veicolo_id}/3432/0/'}
                    # Genera i messaggi per il nuovo geohash
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    longitudine = {"tmstp" : timestamp ,"e": [{"n" : "2" , "v" : f"{lon} " }] }
                    latitudine = {"tmstp" : timestamp ,"e": [{"n" : "1" , "v" : f"{lat} " }] }
                    speed = {"tmstp" : timestamp ,"e": [{"n" : "4" , "v" : f"{traci.vehicle.getSpeed(veicolo_id)} " }] }
                    traffic = {"tmstp" : timestamp ,"e": [{"n" : "1" , "v" : f"{traci.vehicle.getIDCount()} " }] }
                    messages = {
        topics_veicolo['latitudine']: f"{latitudine}", 
        topics_veicolo['longitudine']: f"{longitudine}",
        topics_veicolo['velocità']: f"{speed}",    
        topics_veicolo['traffico']: f"{traffic}",  # Valore dinamico
                 }
                except traci.exceptions.TraCIException as e:
                    print(f"Errore a step {step} con veicolo {veicolo_id}: {str(e)}")

            publish_messages(veicolo, messages)  # Pubblica i messaggi dopo la raccolta

            step += 1
            time.sleep(0.5)  # Mantieni una pausa per rallentare la simulazione

        traci.close()

    except KeyboardInterrupt:
        veicolo.loop_stop()
        veicolo.disconnect()

if __name__ == '__main__':
    run()
