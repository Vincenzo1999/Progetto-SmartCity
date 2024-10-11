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

channel.queue_declare(queue=topics_bs['posizione'], exclusive=True)
channel.queue_declare(queue=topics_bs['traffico'], exclusive=True)
channel.queue_declare(queue=topics_bs['segnale'], exclusive=True)

channel.queue_bind(exchange='topic', queue=topics_bs['posizione'])
channel.queue_bind(exchange='topic', queue=topics_bs['traffico'])
channel.queue_bind(exchange='topic', queue=topics_bs['segnale'])

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {body}")

channel.basic_consume(topics_bs['posizione'])
channel.basic_consume(topics_bs['traffico'])
channel.basic_consume(topics_bs['segnale'])
    

channel.start_consuming()
