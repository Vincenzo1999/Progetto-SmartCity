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

def on_message(channel, method_frame, header_frame, body):
     print(f"Ricevuto il messaggio con body {body.decode()} dal topic {topic}")

time.sleep(5)

credentials = pika.PlainCredentials("guest", 'guest')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host = broker,port=port,credentials=credentials))
channel = connection.channel()
channel.exchange_declare(exchange='topic', exchange_type='topic')

for topic in topics_bs.values():
 channel.queue_declare(queue=topic, exclusive=True)
 channel.queue_bind(exchange='topic', queue=topic)
 channel.basic_consume(topic, on_message_callback= on_message)

 print(f"Sottoscritto al topic {topic}")  

#channel.start_consuming()
try:
   while True: 
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
         channel.basic_publish(exchange='topic', routing_key=topic, body=message)
         print(f"Messaggio {message} inviato!")
      time.sleep(10)
      channel.connection.process_data_events()
except KeyboardInterrupt:
   connection.close()
   