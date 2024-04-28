import requests
import json
from pprint import pprint
import datetime

cinemas = {
    "P5505": "CGR - Carcassonne",
    "P0395": "Le Colisée CGR - Carcassonne",
    "W1150": "Le Familia - Quillan",
    "W0119": "Elysée - Limoux",
    "P8110": "Le Casino - Lavelanet",
    "P0218": "Méga Castillet - Perpignan",
    "P0176": "Castillet - Perpignan",
    "P1115": "Institut Jean Vigo - Perpignan",
    "P1424": "Le Rex - Foix",
    "P8108": "L'Estive - Foix",
    "P8111": "Cinéma Casino - Ax-les-Thermes",
    "P7201": "Rex - Pamiers",
    "P1028": "Véo - Castelnaudary",
    "W0950": "Espace Culturel André Malraux - Mirepoix",
}

url_list = [
    f"https://www.allocine.fr/_/showtimes/theater-{cinema}/d-{i}/"
    for cinema in cinemas
    for i in range(1, 8)
]


# Headers below were used from browser, request returns correctly without any headers. Working browser ones stored here in case of future problems.
headers = {
    "authority": "www.allocine.fr",
    "method": "POST",
    "path": "/_/showtimes/theater-P5505/d-3/",
    "scheme": "https",
    "Accept": "*/*",
    "Accept-Encoding": "json",
    "Accept-Language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
    "Cache-Control": "no-cache",
    "Content-Length": "48",
    "Content-Type": "application/json",
    "Dnt": "1",
    "Origin": "https://www.allocine.fr",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Referer": "https://www.allocine.fr/seance/d-3/salle_gen_csalle=P5505.html",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

# This filters movies to show only the VO ones. This means all results for each day should fit onto a single page.
payload = {"filters": [{"showtimes.version": ["ORIGINAL"]}]}

english_showings = []
all_start_times = []

for url in url_list:
    try:
        page = requests.post(url, json=payload)
        page.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Request failed: {e}")
        raise SystemExit(e)

    data = json.loads(page.text)

    print(f"VO showings found: {len(data['results'])}")

    # Nagivate json, identify movies in English, with showings in VO, and extract start times
    for showings_day in data["results"]:
        if "ENGLISH" in showings_day["movie"]["languages"]:
            if showings_day["showtimes"]["original"]:
                showing_instances = showings_day["showtimes"]["original"]
                for instance in showing_instances:
                    all_start_times.append(instance["startsAt"])

            english_showings.append(showings_day)
print(f"{len(english_showings) = }")
pprint(f"{len(all_start_times) = }")

# for showing in english_showings:
#     print(showing["movie"]["title"])
#     print(showing["movie"]["languages"])

pprint(f"Filters used in request: {data['data']}")

with open("vo_showings.json", "w", encoding="utf8") as f:
    json.dump(english_showings, f, ensure_ascii=False)


# print(page.content)

# with open("24_hours.txt", "w", encoding="utf8") as f:
#     f.writelines(page.text)
