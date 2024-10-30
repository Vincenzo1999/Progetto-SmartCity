import random
import time
import pika
from geolib import geohash
import xml.etree.ElementTree as ET
import traci
import sumolib
import traci.exceptions

# Definizione dei topic e variabili
veicolo_id = "1"
broker = "amqp-broker"
port = 5672
osm_file_path = "/app/simulazione.osm"
geohash_prefix = "sqg0u7"

topics_veicolo = {
    'posizione': f'{geohash_prefix}.{veicolo_id}.3430.0',
    'traffico': f'{geohash_prefix}.{veicolo_id}.3432.0'
}
topics_bs = {
    'posizione': f'{geohash_prefix}.*.3430.0',
    'traffico': f'{geohash_prefix}.*.3432.0'
}

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

# Funzione per aggiornare la route
def route_update(vehicle_id, vehicle_routes):
    original_route = vehicle_routes[vehicle_id]
    next_edge = random.choice(original_route)
    return next_edge

# Callback per la ricezione dei messaggi
def on_message(channel, method_frame, header_frame, body):
    print(f"Ricevuto il messaggio con body {body.decode()} dal topic {method_frame.routing_key}")

# Configurazione connessione RabbitMQ
time.sleep(5)
credentials = pika.PlainCredentials("guest", 'guest')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=broker, port=port, credentials=credentials)
)
channel = connection.channel()
channel.exchange_declare(exchange='topic', exchange_type='topic')

# Dichiarazione e binding delle code ai topic di interesse
for topic in topics_bs.values():
    queue = channel.queue_declare(queue=topic, exclusive=True).method.queue
    channel.queue_bind(exchange='topic', queue=queue, routing_key=topic)
    channel.basic_consume(queue=queue, on_message_callback=on_message, auto_ack=True)
    print(f"Sottoscritto al topic {topic}")

# Inizia la simulazione SUMO
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

                # Aggiorna i topic con il geohash calcolato
                topics_veicolo = {
                    'posizione': f'{geohash_value}/{veicolo_id}/3430/0/',
                    'traffico': f'{geohash_value}/{veicolo_id}/3432/0/'
                }
                # Popola il dizionario dei messaggi con i valori aggiornati
                messages[topics_veicolo['posizione']] = f"Latitudine: {lat}, Longitudine: {lon}, Velocità: {speed}"
                messages[topics_veicolo['traffico']] = f"Traffico: {traffic}"

                # Aggiorna la route se il veicolo è alla fine
                if current_edge == route[-1]:
                    next_edge = route_update(veicolo_id, vehicle_routes)
                    route_find = traci.simulation.findRoute(current_edge, next_edge)
                    if route_find.edges:
                        new_route = [edge for edge in route_find.edges]
                        traci.vehicle.setRoute(veicolo_id, new_route)

            except traci.exceptions.TraCIException as e:
                print(f"Errore a step {step} con veicolo {veicolo_id}: {str(e)}")

        # Pubblica i messaggi su RabbitMQ
        for topic, message in messages.items():
            channel.basic_publish(exchange='topic', routing_key=topic, body=message)
            print(f"Messaggio {message} inviato!")

        time.sleep(1)
        step += 1

except KeyboardInterrupt:
    print("Simulazione interrotta dall'utente.")
finally:
    connection.close()
    traci.close()
