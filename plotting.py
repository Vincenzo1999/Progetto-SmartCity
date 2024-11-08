import matplotlib.pyplot as plt
import numpy as np

def leggi_dati(file_path):
    y = []
    with open(file_path, 'r') as file:
        for line in file:
            columns = line.split()
            y.append(int(columns[1]))  
    return y

file_path_mqtt = "/home/vincenzo/mqtt-txt.txt"  
file_path_amqp = "/home/vincenzo/amqp.txt"

y_data_mqtt = leggi_dati(file_path_mqtt)
y_data_amqp = leggi_dati(file_path_amqp)
media_data_mqtt = sum(y_data_mqtt)/len(y_data_mqtt) 
media_data_amqp = sum(y_data_amqp)/len(y_data_amqp)
y_data=[]
y_data.append(media_data_mqtt)
y_data.append(media_data_amqp)
x_data=[]
x_data.append('MQTT')
x_data.append('AMQP')


plt.xlabel('Protocolli')
plt.ylabel('Payload(Byte)')
plt.title('Grafico dei Dati')
plt.bar(x_data, y_data, color=['red', 'blue'], width=0.8)

plt.show()