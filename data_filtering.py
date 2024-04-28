import json
from pprint import pprint
from datetime import datetime

from movie import Movie

with open("vo_showings.json", "r", encoding="utf8") as f:
    data = json.load(f)

all_movies = {}


def create_movie(item: dict) -> Movie:
    """Creates a Movie object from the raw json data

    Args:
        item (dict): raw movie data from request, single movie at a time

    Returns:
        Movie object
    """
    allocine_id = item["movie"]["id"]
    original_title = item["movie"]["originalTitle"]
    french_title = item["movie"]["title"]
    synopsis = item["movie"]["synopsis"]
    image_poster = item["movie"]["poster"]["url"]
    runtime = item["movie"]["runtime"]
    genres = [genre["tag"].title() for genre in item["movie"]["genres"]]
    languages = [language.title() for language in item["movie"]["languages"]]

    cast = []
    for cast_raw in item["movie"]["cast"]["edges"]:
        try:
            cast_member = cast_raw["node"]["actor"]
            first_name = cast_member["firstName"] or ""
            last_name = cast_member["lastName"] or ""
            name = " ".join([first_name, last_name]).strip()

            cast.append(name)

        except:
            pprint(cast_raw)

    release_date = None
    for release in item["movie"]["releases"]:
        if release["__typename"] == "MovieRelease" and release["releaseDate"]:
            try:
                date_str = release["releaseDate"]["date"]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                release_date = date_obj.strftime("%#dth %B %Y")
                break
            except:
                continue
    if not release_date:
        date_str = str(item["data"]["productionYear"]) + ("-01-01")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        release_date = date_obj.strftime("%#dth %B %Y")

    return Movie(
        allocine_id,
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
    allocine_id = item["movie"]["id"]
    if allocine_id not in all_movies:
        all_movies[allocine_id] = create_movie(item)

print(len(all_movies))

all_keys = sorted([allocine_id for allocine_id in all_movies.keys()])

# for item in all_movies:
#     print(item, all_movies[item].original_title)

pprint(all_keys)

