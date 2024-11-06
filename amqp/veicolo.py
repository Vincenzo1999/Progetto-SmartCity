import random
import time
import pika
from geolib import geohash
import xml.etree.ElementTree as ET
import traci
import sumolib
import traci.exceptions

# Definizione dei topic e variabili
veicolo_id = "56"
broker = "amqp-broker"
port = 5672
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

# Funzione per aggiornare la route
def route_update(vehicle_id, vehicle_routes):
    original_route = vehicle_routes[vehicle_id]
    next_edge = random.choice(original_route)
    return next_edge

# Callback per la ricezione dei messaggi
def on_message(channel, method_frame, header_frame, body):
    print(f"Ricevuto il messaggio con body {body.decode()} dal topic {method_frame.routing_key}")

# Funzione per disiscriversi da un topic
def unsubscribe_from_topic(channel, queue, topic):
    channel.queue_unbind(exchange='topic', queue=queue, routing_key=topic)
    print(f"Disiscritto dal topic {topic}")

# Configurazione connessione RabbitMQ
time.sleep(5)
credentials = pika.PlainCredentials("guest", 'guest')
time.sleep(5)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=broker, port=port, credentials=credentials)
)
channel = connection.channel()
channel.exchange_declare(exchange='topic', exchange_type='topic')

# Inizia la simulazione SUMO
try:
    path = "/app/Stadio.sumocfg"
    traci.start(["sumo", "-c", path, "--step-length", "0.5"])

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

                # Definizione dei topic di base station (BS)
                topics_bs = {
                    'posizione': f'{geohash_value}.*.3430.0.',
                    'traffico': f'{geohash_value}.*.3432.0.',
                    'signal': f'{geohash_value}.*.4.0.'
                }

                # Dichiarazione e binding delle code per ogni topic di BS
                queues = {}
                for key, topic in topics_bs.items():
                    queue_name = f'{key}_queue'  # Nome della coda specifico per ogni topic
                    queue = channel.queue_declare(queue=queue_name, exclusive=True).method.queue
                    queues[key] = queue
                    channel.queue_bind(exchange='topic', queue=queue, routing_key=topic)
                    channel.basic_consume(queue=queue, on_message_callback=on_message, auto_ack=True)
                    print(f"Sottoscritto al topic {topic} con la coda {queue_name}")

                # Controllo e aggiornamento della sottoscrizione in base al geohash
                if geohash_value != previous_geohash:
                    # Disiscrivi dal topic del geohash precedente, se esistente
                    if previous_geohash:
                        old_topics = {
                            'posizione': f'{previous_geohash}.{veicolo_id}.3430.0.',
                            'traffico': f'{previous_geohash}.{veicolo_id}.3432.0.'
                        }
                        for key, topic in old_topics.items():
                            unsubscribe_from_topic(channel, queues[key], topic)

                    # Aggiorna e sottoscrivi ai topic relativi al nuovo geohash
                    new_topics = {
                        'posizione': f'{geohash_value}.*.3430.0.',
                        'traffico': f'{geohash_value}.*.3432.0.',
                        'signal': f'{geohash_value}.*.4.0.'
                    }
                    for key, topic in new_topics.items():
                        channel.queue_bind(exchange='topic', queue=queues[key], routing_key=topic)
                        print(f"Sottoscritto al topic {topic} con la coda {queues[key]}")

                    previous_geohash = geohash_value  # Aggiorna il geohash precedente

                # Preparazione dei messaggi per il nuovo geohash
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                longitudine = {"tmstp": timestamp, "e": [{"n": "2", "v": f"{lon} "}]}
                latitudine = {"tmstp": timestamp, "e": [{"n": "1", "v": f"{lat} "}]}
                speed = {"tmstp": timestamp, "e": [{"n": "4", "v": f"{traci.vehicle.getSpeed(veicolo_id)} "}]}
                traffic = {"tmstp": timestamp, "e": [{"n": "1", "v": f"{traci.vehicle.getIDCount()} "}]}

                topics_veicolo = {
                    'latitudine': f'{geohash_value}.{veicolo_id}.3430.0.',
                    'longitudine': f'{geohash_value}.{veicolo_id}.3430.0.',
                    'velocità': f'{geohash_value}.{veicolo_id}.3430.0.',
                    'traffico': f'{geohash_value}.{veicolo_id}.3432.0.'
                }

                messages = {
                    topics_veicolo['latitudine']: str(latitudine), 
                    topics_veicolo['longitudine']: str(longitudine),
                    topics_veicolo['velocità']: str(speed),
                    topics_veicolo['traffico']: str(traffic)
                }

            except traci.exceptions.TraCIException as e:
                print(f"Errore a step {step} con veicolo {veicolo_id}: {str(e)}")

            # Pubblica i messaggi AMQP
            for topic, message in messages.items():
                channel.basic_publish(exchange='topic', routing_key=topic, body=message)
                print(f"Messaggio {topic}{message} inviato")
            time.sleep(10)

        channel.connection.process_data_events()
        step += 1
        time.sleep(0.5)  # Mantieni una pausa per rallentare la simulazione

    traci.close()
except KeyboardInterrupt:
    print("Simulazione interrotta dall'utente.")
finally:
    connection.close()
    traci.close()
