# genera la mappa comune → lista di id_station e la salva nel file station_map.json
import requests
import json

url = "https://dati.arpa.puglia.it/api/v1/stations?format=GEOJSON"
response = requests.get(url)
data = response.json()

station_map = {}
for feature in data["features"]:
    props = feature["properties"]
    comune = props.get("comune")
    id_station = props.get("id_station")
    if comune and id_station:
        station_map.setdefault(comune, []).append(id_station)

with open("station_map.json", "w", encoding="utf-8") as f:
    json.dump(station_map, f, ensure_ascii=False, indent=2)

print("Mappa salvata in station_map.json")
