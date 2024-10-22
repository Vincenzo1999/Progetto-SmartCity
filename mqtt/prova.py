import traci
import random
import sumolib
import subprocess

# Percorso al file di configurazione SUMO
path = "/home/vincenzo/simulazione _osm/simulazione.sumocfg"
traci.start(["sumo-gui", "-c", path, "--step-length", "1"])

# Leggi la rete
#net = sumolib.net.readNet("/home/vincenzo/Sumo/2024-10-17-17-04-06/osm.net.xml")



while traci.simulation.getMinExpectedNumber() > 0:
  traci.simulationStep()
# Ottieni la lista delle corsie e crea una lista degli edge per i veicoli passeggeri
  lane_list = traci.lane.getIDList()
  edge_list = []

  for lane in lane_list:
    
    allowed_vehicles = traci.lane.getAllowed(lane)
    if 'passenger' in allowed_vehicles:
        edge = traci.lane.getEdgeID(lane)
        edge_list.append(edge)

# Seleziona casualmente un edge di partenza e uno di arrivo
  start_edge = random.choice(edge_list)
  end_edge = random.choice(edge_list)

# Esegui findAllRoutes.py per ottenere la rotta
  cmd = ["python3", "findAllRoutes.py", "-n", path, "-s", start_edge, "-t", end_edge]
  result = subprocess.run(cmd, capture_output=True, text=True)

# Stampa l'output del comando
  print("Output di findAllRoutes.py:", result.stdout)
    # Ottieni la lista dei veicoli nella simulazione
  veicoli = traci.vehicle.getIDList()

  if veicoli:  # Verifica se ci sono veicoli nella simulazione
        # Seleziona casualmente un veicolo
        veicolo = random.choice(veicoli)
        
        # Verifica l'output di findAllRoutes.py e imposta la nuova rotta
        new_route = result.stdout.strip().split("\n")
        if new_route and new_route[0] != "":
            traci.vehicle.setRoute(veicolo, new_route)

traci.close()