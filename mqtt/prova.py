import requests
import random

# API e informazioni sulla bounding box
api = "pk.3f5c5de68b06b081a2e814e3b186f773"
latitudine_max = 38.1194325
latitudine_min = 38.109894
longitudine_max = 15.6574058
longitudine_min = 15.6439948
URL = f"http://www.opencellid.org/cell/getInArea?key={api}&BBOX={latitudine_min},{longitudine_min},{latitudine_max},{longitudine_max}&format=json"

try:
    # Effettua la richiesta
    response = requests.get(URL)

    # Controlla se la richiesta è andata a buon fine
    if response.status_code == 200:
        # Converti la risposta in formato JSON
        messaggio_json = response.json()

        # Inizializza un array per memorizzare i dati delle celle
        cell_data_array = []

        # Estrai e memorizza 'cellid' e le coordinate in un array
        for cell in messaggio_json.get("cells", []):
            cellid = cell.get("cellid")
            lat = cell.get("lat")
            lon = cell.get("lon")

            if cellid is not None and lat is not None and lon is not None:
                cell_data_array.append({
                    "cellid": cellid,
                    "lat": lat, 
                    "lon": lon
                    })

        # Se ci sono celle disponibili, scegli una cella casuale e stampa le informazioni
        if cell_data_array:
            cella = random.choice(cell_data_array)  # Seleziona una cella casuale
            cellid = cella["cellid"]
            latitudine = cella["lat"]
            longitudine = cella ["lon"]

            # Stampa il cellid e le coordinate della cella scelta
            print(cell_data_array)
            print(f"Cella Casuale: CellID = {cellid}, Coordinate = {latitudine} {longitudine}")
        else:
            print("Nessuna cella trovata nell'area specificata.")

    else:
        # Gestione di errori in caso di risposta non corretta
        print(f"Errore: {response.status_code}")
        print("Dettagli:", response.text)

except requests.exceptions.RequestException as e:
    # Gestione degli errori di connessione o timeout
    print(f"Errore di connessione: {e}")