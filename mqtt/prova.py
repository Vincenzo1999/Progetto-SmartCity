import traci
import sumolib
import random
import time
import traci.exceptions



# Connect to SUMO simulation
traci.start(["sumo-gui", "-c", "/home/vincenzo/Simulazione/Stadio.sumocfg"])

# Simulation loop
step = 0
while step < 1000:
    traci.simulationStep()
    # Your simulation logic here
    step += 1

# Close TraCI connection
traci.close()