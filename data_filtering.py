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


# Loop through all scraped movie/showings in json. Each item relates to a single cinema on a single day,and will contain one movie, and one or more showings for that movie
for item in data:
    cinema_id = "P8110"
    # Set movie_id
    movie_id = item["movie"]["id"]
    # Check if movie is in database, if not then add it
    if not movie_man.movie_already_in_database(movie_id):
        movie_man.add_new_movie(item)
    # Check if showings are in database, if not then add them to show_man.new_showings list
    show_man.create_showing(item, cinema_id)
    break


# print(show_man.new_showings)
# pprint(show_man.current_showings)
# break
show_man.add_new_showings_to_database()

# print(f"Total new movies added: {len(movie_man.new_movies)}")

# all_keys = sorted(movie_man.current_movie_ids)

# # for item in all_movies:
# #     print(item, all_movies[item].original_title)

# print(f"All movie_ids: {all_keys}")
