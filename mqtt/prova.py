import traci
import sumolib
import random
import time
import traci.exceptions

# Percorso al file di configurazione SUMO
path = "/home/samu/Scaricati/simulazione _osm/simulazione _osm/simulazione.sumocfg"

# Avvia la simulazione
traci.start(["sumo", "-c", path, "--step-length", "1"])

# Crea un dizionario per le rotte dei veicoli
vehicle_routes = {}
for vehicle in sumolib.xml.parse("/home/samu/Scaricati/simulazione _osm/simulazione _osm/simulazione.rou.xml", "vehicle"):
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
            x,y = traci.vehicle.getPosition(veicolo_id)
            lat, lon = traci.simulation.convertGeo(x,y)
            speed = traci.vehicle.getSpeed(veicolo_id)

            print(f"Step {step} - Veicolo {veicolo_id}: emissione CO2 = {emission}, route = {route}")
            print(f"Step {step} - Veicolo {veicolo_id}: traffic= {traffic}, route = {route}")
            print(f"Step {step} - Veicolo {veicolo_id}: lat = {lat}, route = {route}")
            print(f"Step {step} - Veicolo {veicolo_id}: lon = {lon}, route = {route}")
            print(f"Step {step} - Veicolo {veicolo_id}: speed = {speed}, route = {route}")



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
