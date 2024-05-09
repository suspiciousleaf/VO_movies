from requests import Session
from pprint import pprint
from creds import *

s = Session()

# Search movie with title, get IMDB ref to find more details. Includes url to poster. response["results"][0]["id"]
title = "Ghostbusters: Frozen Empire"
year = 2023
ref_url = f"https://moviesdatabase.p.rapidapi.com/titles/search/title/{title}"

querystring = {
    "exact": "false",
    "endYear": f"{year+1}",
    "startYear": f"{year-1}",
    "titleType": "movie",
}

headers = {
    "X-RapidAPI-Key": movies_db_api_key,
    "X-RapidAPI-Host": "moviesdatabase.p.rapidapi.com",
}

response = s.get(ref_url, headers=headers, params=querystring).json()

imdb_ref = response["results"][0]["id"]
print(f"{imdb_ref = }")

# Get IMDB rating

url = f"https://moviesdatabase.p.rapidapi.com/titles/{imdb_ref}?info=rating"

response = s.get(url, headers=headers).json()

rating = response["results"]["ratingsSummary"]["aggregateRating"]
print(f"{rating = }")

# Synopsis

url = f"https://moviesdatabase.p.rapidapi.com/titles/{imdb_ref}?info=plot"

response = s.get(url, headers=headers).json()

synopsis = response["results"]["plot"]["plotText"]["plainText"]
print(f"{synopsis = }")
