import json
from pprint import pprint

from movie import Movie

with open("vo_showings.json", "r", encoding="utf8") as f:
    data = json.load(f)

movie_list = []

for item in data:
    original_title = item["movie"]["originalTitle"]
    french_title = item["movie"]["title"]
    synopsis = item["movie"]["synopsis"]
    image_poster = item["movie"]["poster"]["url"]
    runtime = item["movie"]["runtime"]
    genres = [genre["tag"].title() for genre in item["movie"]["genres"]]
    languages = [language.title() for language in item["movie"]["languages"]]

    cast = []
    for cast_raw in item["movie"]["cast"]["edges"]:
        cast_member = cast_raw["node"]["actor"]
        name = " ".join([cast_member["firstName"], cast_member["lastName"]])
        cast.append(name)

    release_year = None
    for release in item["movie"]["releases"]:
        if release["__typename"] == "MovieRelease":
            release_year = release["releaseDate"]["date"]
            break
    if not release_year:
        release_year = str(item["data"]["productionYear"])

    movie_list.append(
        Movie(
            original_title,
            french_title,
            image_poster,
            runtime,
            synopsis,
            cast,
            languages,
            genres,
            release_year,
        )
    )

for item in movie_list:
    print(item)
    print("\n")
