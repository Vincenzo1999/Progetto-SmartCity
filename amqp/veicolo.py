import random
import time
import pika
from geolib import geohash

topics_veicolo = { 'posizione' : 'veicolo.posizione', 
            'velocità' : 'veicolo.velocità'  }
topics_bs = { 'posizione' : 'bs.posizione', 
          'traffico' : 'bs.traffico',
            'segnale' : 'bs.signal'  }
veicolo_id = f"veicolo {random.randint(0,100)}"
broker = "amqp-broker"
port = 5672

latitudine_max = 38.1194325
latitudine_min = 38.109894
longitudine_max = 15.6574058
longitudine_min = 15.6439948

time.sleep(5)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host = broker))
channel = connection.channel()

channel.exchange_declare(exchange='topic', exchange_type='topic')

result = channel.queue_declare(queue=topics_bs['posizione'], exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='topic', queue=topics_bs['posizione'])

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {body}")

channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()
"""

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
        time.sleep(2)
        for topic in topics_bs.values():
         client.subscribe(topic)
         print(f"Mi sono sottoscritto al topic {topic}")
        # Pubblica il messaggio
       
    else:
        print(f"Failed to connect, return code {reason_code}")

def publish(client):
    
    latitudine = random.uniform(latitudine_min,latitudine_max)
    longitudine = random.uniform(longitudine_min,longitudine_max)
    position_veicolo = geohash.encode (latitudine,longitudine,7)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    speed = {"tmstp" : timestamp, "e": [{ "n" : "3430/0/4" , "v" : f"{random.randint(0, 60)}" }] }
    
    messages = {
        topics_veicolo['posizione']: f"Posizione: {position_veicolo}",  # Valore dinamico
        topics_veicolo['velocità']: f"Velocità: {speed} km/h"  # Valore dinamico
    }
    
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
    veicolo.connect(broker, port,5)
   
    veicolo.loop_start()
    
    try:
        while True:
            publish(veicolo)
            time.sleep(5)  # Ritardo di 5 secondi tra ogni pubblicazione
    except KeyboardInterrupt:
        veicolo.loop_stop()  # Ferma il thread MQTT
        veicolo.disconnect()  # Disconnette dal broker
   

if __name__ == '__main__':
    run()
"""