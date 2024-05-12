from requests import Session
from pprint import pprint
from creds import *

s = Session()

movies = [
    {"title": "LaRoy, Texas", "year": 2023},
    {"title": "The Dead Don't Hurt", "year": 2023},
    {"title": "Madame Butterfly (Metropolitan Opera)", "year": 2016},
    {
        "title": "John Singer Sargent: Fashion and Swagger",
        "year": 2024,
    },
    {"title": "Kingdom of the Planet of the Apes", "year": 2024},
    # {"title": "Transformers: 40th Anniversary Event", "year": 2012},
    {"title": "Back To Black", "year": 2024},
]


for movie in movies:
    ref_url = (
        f"https://moviesdatabase.p.rapidapi.com/titles/search/title/{movie['title']}"
    )
    queryparams = {
        "exact": "false",
        "endYear": f"{movie['year']}",
        "startYear": f"{movie['year']-1}",
        "titleType": "movie",
    }

    headers = {
        "X-RapidAPI-Key": movies_db_api_key,
        "X-RapidAPI-Host": "moviesdatabase.p.rapidapi.com",
    }

    # IMDB ref must be identified first, then other details can be retrieved
    response = s.get(ref_url, headers=headers, params=queryparams)
    response.raise_for_status()
    if response.json()["results"]:
        movie["imdb_ref"] = response.json()["results"][0]["id"]
    # If no results found using title and year, try again without the year.
    else:
        queryparams = {
            "exact": "false",
            "titleType": "movie",
        }
        response = s.get(ref_url, headers=headers, params=queryparams)
        response.raise_for_status()
        # if response.json()["results"]:
        #     movie["imdb_ref"] = response.json()["results"][0]["id"]
        # else:
        #     raise Exception("Movie not found")

    # Dict to store each of the required details, and the keys required to access that data in the json
    required_details = {
        "rating": ("results", "ratingsSummary", "aggregateRating"),
        "plot": ("results", "plot", "plotText", "plainText"),
    }

    for detail, keys in required_details.items():
        try:

            query_url = f"https://moviesdatabase.p.rapidapi.com/titles/{movie['imdb_ref']}?info={detail}"

            response = s.get(query_url, headers=headers)

            response.raise_for_status()
            nested_data = response.json()
            for key in keys:
                nested_data = nested_data.get(key, {})

            if detail == "plot":
                detail = "synopsis"
            movie[detail] = nested_data
        except:
            movie[detail] = None

    pprint(movie)
