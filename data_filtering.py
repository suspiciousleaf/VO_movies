import json
from pprint import pprint
from datetime import datetime

from movie import Movie

with open("vo_showings.json", "r", encoding="utf8") as f:
    data = json.load(f)

movie_list = []


def create_movie(item: dict) -> Movie:
    """Creates a Movie object from the raw json data

    Args:
        item (dict): raw data from request

    Returns:
        Movie object
    """
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

    release_date = None
    for release in item["movie"]["releases"]:
        if release["__typename"] == "MovieRelease":
            date_str = release["releaseDate"]["date"]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            release_date = date_obj.strftime("%#dth %B %Y")
            break
    if not release_date:
        date_str = str(item["data"]["productionYear"]) + ("-01-01")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        release_date = date_obj.strftime("%#dth %B %Y")

    return Movie(
        original_title,
        french_title,
        image_poster,
        runtime,
        synopsis,
        cast,
        languages,
        genres,
        release_date,
    )


for item in data:
    movie_list.append(create_movie(item))


for item in movie_list:
    print(item)
    print("\n")
