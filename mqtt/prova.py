import traci
import sumolib
import random
import time

import traci.exceptions

# Percorso al file di configurazione SUMO
path = "/home/vincenzo/simulazione _osm/simulazione.sumocfg"

# Avvia la simulazione
traci.start(["sumo", "-c", path, "--step-length", "1"])
vehicle_routes = {}
for vehicle in sumolib.xml.parse("/home/vincenzo/simulazione _osm/simulazione.rou.xml", "vehicle"):
    route = vehicle.route[0]  # Accesso al primo (e unico) elemento 'route'
    edges = route.edges.split()  # Ottieni la lista degli edges della route
    vehicle_routes[vehicle.id] = edges  # Aggiungi il veicolo e la sua route al dizionario
veicolo_id="1"#random.choice(list(vehicle_routes.keys()))
def route_update(vehicle_id,end_edge):
    new_destination_list=[]
    for other_vehicle_id, other_route in vehicle_routes.items():
      if other_vehicle_id != vehicle_id and end_edge in other_route:
                        # Trova l'indice dell'edge corrente nella route
        index = other_route.index(end_edge)
                        # Verifica se esiste un edge successivo
        if index + 1 < len(other_route):
          next_edge = other_route[index + 1]
                            # Aggiorna la route del veicolo corrente
          new_destination_list.append(next_edge)
        else:
          print("errore index")    # Aggiungi il prossimo edge alla route
    new_destination= random.choice(new_destination_list)
    #traci.vehicle.changeTarget(veicolo_id,new_destination)
    return new_destination 

step=0
while step<1000:
 traci.simulationStep()
 try: 
    current_edge = traci.vehicle.getRoadID(veicolo_id)
    route= traci.vehicle.getRoute(veicolo_id)
    emission = traci.vehicle.getCO2Emission(veicolo_id)
    
    print(emission,route)
    if current_edge==route[-1]:
       next_edge = route_update(veicolo_id,current_edge)
       
       
       route_find = traci.simulation.findRoute(current_edge,next_edge)
       if route_find.edges != "":
        new_route=[]
        for edge in route_find.edges:
          new_route.append(edge)
        print(f"new_route:{new_route}")  
        traci.vehicle.setRoute(veicolo_id,new_route)
       else:
        print("non ci sono più edge da aggiungere") 
        
       

    step += 1   
 except traci.exceptions.TraCIException: 
  print(f"{step} ciao")
  time.sleep(1)
  step += 1

 

traci.close()

