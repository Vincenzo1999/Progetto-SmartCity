import matplotlib.pyplot as plt

def leggi_dati(file_path):
    y = []
    with open(file_path, 'r') as file:
        for line in file:
            columns = line.split()
            if columns:  
                try:
                    y.append(int(columns[0]))  
                except ValueError:
                    print(f"Valore non valido trovato nella riga: {line.strip()}")
    return y

file_path_mqtt_bs_frame = "/home/vincenzo/Scrivania/Progetto-SmartCity/mqtt_traffic_bs.txt"
file_path_amqp_bs_frame= "/home/vincenzo/Scrivania/Progetto-SmartCity/amqp_traffic_bs.txt"
file_path_mqtt_veicolo_frame = "/home/vincenzo/Scrivania/Progetto-SmartCity/mqtt_traffic_vehicle.txt"
file_path_amqp_veicolo_frame = "/home/vincenzo/Scrivania/Progetto-SmartCity/amqp_traffic_vehicle.txt"
file_path_mqtt_bs_msg = "/home/vincenzo/Scrivania/Progetto-SmartCity/mqtt_traffic_bs_message.txt"
file_path_amqp_bs_msg = "/home/vincenzo/Scrivania/Progetto-SmartCity/amqp_traffic_bs_message.txt"
file_path_mqtt_veicolo_msg= "/home/vincenzo/Scrivania/Progetto-SmartCity/mqtt_traffic_vehicle_message.txt"
file_path_amqp_veicolo_msg= "/home/vincenzo/Scrivania/Progetto-SmartCity/amqp_traffic_vehicle_message.txt"

y_data_mqtt_bs_frame = leggi_dati(file_path_mqtt_bs_frame)
y_data_amqp_bs_frame = leggi_dati(file_path_amqp_bs_frame)
y_data_mqtt_vehicle_frame = leggi_dati(file_path_mqtt_veicolo_frame)
y_data_amqp_vehicle_frame = leggi_dati(file_path_amqp_veicolo_frame)
y_data_mqtt_bs_msg = leggi_dati(file_path_mqtt_bs_msg)
y_data_amqp_bs_msg = leggi_dati(file_path_amqp_bs_msg)
y_data_mqtt_vehicle_msg = leggi_dati(file_path_mqtt_veicolo_msg)
y_data_amqp_vehicle_msg = leggi_dati(file_path_amqp_veicolo_msg)

# Somma dei valori per AMQP
y_data_veicolo_frame = [
    sum(y_data_mqtt_vehicle_frame), 
    sum(y_data_amqp_vehicle_frame)
]
y_data_bs_frame = [
    sum(y_data_mqtt_bs_frame),
    sum(y_data_amqp_bs_frame)
]

y_data_veicolo_msg = [
    sum(y_data_mqtt_vehicle_msg), 
    sum(y_data_amqp_vehicle_msg)
]
y_data_bs_msg = [
    sum(y_data_mqtt_bs_msg),
    sum(y_data_amqp_bs_msg)
]

x_labels = ['MQTT', 'AMQP']

plt.figure(figsize=(12, 10))  


plt.subplot(2, 2, 1)
plt.bar(x_labels, y_data_veicolo_frame, color=['red', 'blue'], width=0.5)
plt.xlabel('Protocolli')
plt.ylabel('Pacchetti (Byte)')
plt.title('Pacchetti Veicolo')


plt.subplot(2, 2, 2)
plt.bar(x_labels, y_data_bs_frame, color=['green', 'purple'], width=0.5)
plt.xlabel('Protocolli')
plt.ylabel('Pacchetti (Byte)')
plt.title('Pacchetti Base Station')


plt.subplot(2, 2, 3)
plt.bar(x_labels, y_data_veicolo_msg, color=['red', 'blue'], width=0.5)
plt.xlabel('Protocolli')
plt.ylabel('Payload (Byte)')
plt.title('Payload Veicolo (Messaggi)')


plt.subplot(2, 2, 4)
plt.bar(x_labels, y_data_bs_msg, color=['green', 'purple'], width=0.5)
plt.xlabel('Protocolli')
plt.ylabel('Payload (Byte)')
plt.title('Payload Base Station (Messaggi)')

plt.tight_layout()  
plt.show()
