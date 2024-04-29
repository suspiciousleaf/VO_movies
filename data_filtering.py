import json
from pprint import pprint
from datetime import datetime

from movie import MovieManager
from showing import ShowingsManager

with open("vo_showings.json", "r", encoding="utf8") as f:
    data = json.load(f)

# all_movies = {}

movie_man = MovieManager()
show_man = ShowingsManager()


# Loop through all scraped movie/showings in json
for item in data:
    cinema_id = "P8110"
    # Set movie_id
    movie_id = item["movie"]["id"]
    # Check if movie is in database, if not then add it
    if not movie_man.verify_movie_id_in_current_movies(movie_id):
        movie_man.add_new_movie(item)
    # Check if showings are in database, if not then add them
    show_man.create_showing(item, cinema_id)


# print(show_man.new_showings)
pprint(show_man.current_showings)
# break


# print(f"Total new movies added: {len(movie_man.new_movies)}")

# all_keys = sorted(movie_man.current_movie_ids)

# # for item in all_movies:
# #     print(item, all_movies[item].original_title)

# print(f"All movie_ids: {all_keys}")
