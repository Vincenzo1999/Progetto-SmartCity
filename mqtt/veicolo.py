import random
import time
from paho.mqtt import client as mqtt_client
from geolib import geohash
import xml.etree.ElementTree as ET
import traci
import sumolib
import traci.exceptions


topics_bs = {'posizione': f'{geohash}/+/3430/0/',
             'traffico': f'{geohash}/+/3432/0/',
             'segnale': f'{geohash}/+/4/0/'}

broker = "mqtt-broker"
port = 1883
veicolo_id= "1"
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

    # Stampa i risultati
    print(f"Min Latitudine: {min_latitude}, Min Longitudine: {min_longitude}")
    print(f"Max Latitudine: {max_latitude}, Max Longitudine: {max_longitude}")
else:
    print("La bounding box non è presente nel file OSM.")


def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
        time.sleep(2)
        for topic in topics_bs.values():
            client.subscribe(topic)
            print(f"Mi sono sottoscritto al topic {topic}")
    else:
        print(f"Failed to connect, return code {reason_code}")


def publish(client):
    path = "/app/simulazione.sumocfg"

    # Avvia la simulazione
    traci.start(["sumo", "-c", path, "--step-length", "1"])

    # Crea un dizionario per le rotte dei veicoli
    vehicle_routes = {}
    for vehicle in sumolib.xml.parse("/app/simulazione.rou.xml", "vehicle"):
        route = vehicle.route[0]
        edges = route.edges.split()
        vehicle_routes[vehicle.id] = edges

    # Funzione per aggiornare la route di un veicolo
    def route_update(vehicle_id):
        original_route = vehicle_routes[vehicle_id]
        # Seleziona un edge casuale per mantenere il veicolo attivo
        next_edge = random.choice(original_route)
        return next_edge

    # Lista dei veicoli attivi
    active_vehicles = set()

    # Ciclo di simulazione
    step = 0
    while step < 2000:  # Aumenta il limite della simulazione se necessario
        traci.simulationStep()

        # Aggiungi nuovi veicoli solo se ci sono meno di un certo limite
        new_vehicles = traci.simulation.getDepartedIDList()
        active_vehicles.update(new_vehicles)
       

        # Itera sui veicoli attivi
        for veicolo_id in list(active_vehicles):
            try:
                current_edge = traci.vehicle.getRoadID(veicolo_id)
                route = traci.vehicle.getRoute(veicolo_id)
                emission = traci.vehicle.getCO2Emission(veicolo_id)
                traffic = traci.vehicle.getIDCount()
                x, y = traci.vehicle.getPosition(veicolo_id)
                lat, lon = traci.simulation.convertGeo(x, y)
                speed = traci.vehicle.getSpeed(veicolo_id)

                #print(f"Step {step} - Veicolo {veicolo_id}: emissione CO2 = {emission}, route = {route}")
                #print(f"Step {step} - Veicolo {veicolo_id}: traffic = {traffic}, route = {route}")
                #print(f"Step {step} - Veicolo {veicolo_id}: lat = {lat}, route = {route}")
                #print(f"Step {step} - Veicolo {veicolo_id}: lon = {lon}, route = {route}")
                #print(f"Step {step} - Veicolo {veicolo_id}: speed = {speed}, route = {route}")
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                speed_veicolo = {"tmstp": timestamp, "e": [{"n": "4", "v": f"{speed}"}]}
                latitudine_veicolo = {"tmstp": timestamp, "e": [{"n": "1", "v": f"{lat}"}]}
                longitudine_veicolo = {"tmstp": timestamp, "e": [{"n": "2", "v": f"{lon}"}]}
                emissione_veicolo = {"tmstp": timestamp, "e": [{"n": "3430/0/4", "v": f"{emission}"}]}
                traffico_veicolo = {"tmstp": timestamp, "e": [{"n": "3430/0/4", "v": f"{traffic}"}]}
                geohash = geohash.decode(latitudine_veicolo,longitudine_veicolo,6)
                
                topics_veicolo = {'posizione': f'{geohash}/{veicolo_id}/3430/0/',
                  'traffico': f'{geohash}/{veicolo_id}/3432/0/'}
                
                messages = {
                    topics_veicolo['posizione']: f"Latitudine: {latitudine_veicolo}",
                    topics_veicolo['posizione']: f"Longitudine: {longitudine_veicolo}",
                    topics_veicolo['posizione']: f"Velocità: {speed_veicolo}",  
                    topics_veicolo['traffico']: f"Traffico: {traffico_veicolo}"  # Valore dinamico
                }

                # Se il veicolo è alla fine della route, reindirizzalo
                if current_edge == route[-1]:
                    next_edge = route_update(veicolo_id)
                    route_find = traci.simulation.findRoute(current_edge, next_edge)
                    if route_find.edges:
                        new_route = [edge for edge in route_find.edges]
                        traci.vehicle.setRoute(veicolo_id, new_route)

            except traci.exceptions.TraCIException as e:
                print(f"Errore a step {step} con veicolo {veicolo_id}: {str(e)}")

        step += 1
        time.sleep(0.5)  # Mantieni una pausa per rallentare la simulazione

    traci.close()

    for topic, message in messages.items():
        result = client.publish(topic, message)
        # Controllo se il messaggio è stato pubblicato con successo
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            print(f"Messaggio '{message}' inviato al topic '{topic}'")
        else:
            print(f"Errore nell'invio del messaggio al topic '{topic}'. Codice errore: {result.rc}")


def on_message(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")


def run():
    veicolo = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, veicolo_id)
    time.sleep(5)
    veicolo.on_connect = on_connect
    veicolo.on_message = on_message
    veicolo.connect(broker, port, 5)

    veicolo.loop_start()

    try:
        
     publish(veicolo)
            
    except KeyboardInterrupt:
        veicolo.loop_stop()  # Ferma il thread MQTT
        veicolo.disconnect()  # Disconnette dal broker


if __name__ == '__main__':
    run()
