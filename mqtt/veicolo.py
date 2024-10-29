import random
import time
from paho.mqtt import client as mqtt_client
from geolib import geohash
import xml.etree.ElementTree as ET
import traci
import sumolib
import traci.exceptions

# Definizione dei topic per il broker
topics_bs = {
    'posizione': f'geohash/+/3430/0/',
    'traffico': f'geohash/+/3432/0/',
    'segnale': f'geohash/+/4/0/'
}

broker = "mqtt-broker"
port = 1883

# Percorso del file .osm
osm_file_path = "/app/simulazione.osm"

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

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print("Connesso al broker MQTT!")
        time.sleep(2)
        for topic in topics_bs.values():
            client.subscribe(topic)
            print(f"Mi sono sottoscritto al topic {topic}")
    else:
        print(f"Connessione fallita, codice di ritorno {reason_code}")

# Funzione per aggiornare la route di un veicolo
def route_update(vehicle_id, vehicle_routes):
    original_route = vehicle_routes[vehicle_id]
    next_edge = random.choice(original_route)
    return next_edge

# Funzione per ricevere messaggi
def on_message(client, userdata, message):
    print(f"Messaggio ricevuto '{message.payload.decode()}' sul topic '{message.topic}'")

def publish_messages(client, messages):
    for topic, message in messages.items():
        result = client.publish(topic, message)
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            print(f"Messaggio '{message}' inviato al topic '{topic}'")
        else:
            print(f"Errore nell'invio del messaggio al topic '{topic}'. Codice errore: {result.rc}")

def run():
    veicolo_id = "0"
    veicolo = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, veicolo_id)
    time.sleep(5)
    veicolo.on_connect = on_connect
    veicolo.on_message = on_message
    veicolo.connect(broker, port, 5)

    veicolo.loop_start()

    try:
        path = "/app/simulazione.sumocfg"
        traci.start(["sumo", "-c", path, "--step-length", "1"])

        vehicle_routes = {}
        for vehicle in sumolib.xml.parse("/app/simulazione.rou.xml", "vehicle"):
            route = vehicle.route[0]
            edges = route.edges.split()
            vehicle_routes[vehicle.id] = edges

        active_vehicles = set()
        step = 0

        while step < 2000:  # Aumenta il limite della simulazione se necessario
            traci.simulationStep()
            new_vehicles = traci.simulation.getDepartedIDList()
            active_vehicles.update(new_vehicles)

            messages = {}  # Inizializza il dizionario dei messaggi

            for veicolo_id in list(active_vehicles):
                try:
                    current_edge = traci.vehicle.getRoadID(veicolo_id)
                    route = traci.vehicle.getRoute(veicolo_id)
                    emission = traci.vehicle.getCO2Emission(veicolo_id)
                    traffic = traci.vehicle.getIDCount()
                    x, y = traci.vehicle.getPosition(veicolo_id)
                    lat, lon = traci.simulation.convertGeo(x, y)
                    speed = traci.vehicle.getSpeed(veicolo_id)

                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    geohash_value = geohash.encode(lat, lon, 6)

                    topics_veicolo = {
                        'posizione': f'{geohash_value}/{veicolo_id}/3430/0/',
                        'traffico': f'{geohash_value}/{veicolo_id}/3432/0/'
                    }

                    messages[topics_veicolo['posizione']] = f"Latitudine: {lat}, Longitudine: {lon}, Velocità: {speed}"
                    messages[topics_veicolo['traffico']] = f"Traffico: {traffic}"

                    if current_edge == route[-1]:
                        next_edge = route_update(veicolo_id, vehicle_routes)
                        route_find = traci.simulation.findRoute(current_edge, next_edge)
                        if route_find.edges:
                            new_route = [edge for edge in route_find.edges]
                            traci.vehicle.setRoute(veicolo_id, new_route)

                except traci.exceptions.TraCIException as e:
                    print(f"Errore a step {step} con veicolo {veicolo_id}: {str(e)}")

            publish_messages(veicolo, messages)  # Pubblica i messaggi dopo la raccolta

            step += 1
            time.sleep(0.5)  # Mantieni una pausa per rallentare la simulazione

        traci.close()

    except KeyboardInterrupt:
        veicolo.loop_stop()  # Ferma il thread MQTT
        veicolo.disconnect()  # Disconnette dal broker

if __name__ == '__main__':
    run()
