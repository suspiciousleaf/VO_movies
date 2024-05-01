import requests
import json
from pprint import pprint
from creds import *
from cinema import CinemaManager

cinema_man = CinemaManager()


# cinemas = {
#     "P5505": "CGR - Carcassonne",
#     "P0395": "Le Colisée CGR - Carcassonne",
#     "W1150": "Le Familia - Quillan",
#     "W0119": "Elysée - Limoux",
#     "P8110": "Le Casino - Lavelanet",
#     "P0218": "Méga Castillet - Perpignan",
#     "P0176": "Castillet - Perpignan",
#     "P1115": "Institut Jean Vigo - Perpignan",
#     "P1424": "Le Rex - Foix",
#     "P8108": "L'Estive - Foix",
#     "P8111": "Cinéma Casino - Ax-les-Thermes",
#     "P7201": "Rex - Pamiers",
#     "P1028": "Véo - Castelnaudary",
#     "W0950": "Espace Culturel André Malraux - Mirepoix",
# }

urls_per_cinema = {
    cinema: [
        f"https://www.allocine.fr/_/showtimes/theater-{cinema}/d-{i}/"
        for i in range(1, 8)
    ]
    for cinema in cinema_man
}


english_showings = []
cinema_id = "P5505"
for target_url in urls_per_cinema[cinema_id]:
    base_url = "https://api.scrapingant.com/v2/general"
    payload = {"filters": [{"showtimes.version": ["ORIGINAL"]}]}
    params = {
        "url": target_url,
        "x-api-key": scraping_ant_api_key,
        "proxy_country": "FR",
        "browser": "false",
        "proxy_country": "FR",
    }

    response = requests.post(base_url, params=params, json=payload)

    if response.status_code == 200:
        data = response.json()
        for showings_day in data["results"]:
            if "ENGLISH" in showings_day["movie"]["languages"]:
                if showings_day["showtimes"]["original"]:
                    english_showings.append(showings_day)
    else:
        print("Error:", response.status_code)
    break


with open("vo_showings_2.json", "w", encoding="utf8") as f:
    json.dump(english_showings, f, ensure_ascii=False)

#! This works, wrap in a class
