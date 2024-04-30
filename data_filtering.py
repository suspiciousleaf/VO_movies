import json
from pprint import pprint
from datetime import datetime

from movie import MovieManager
from showing import ShowingsManager

with open("vo_showings.json", "r", encoding="utf8") as f:
    data = json.load(f)

movie_man = MovieManager()
show_man = ShowingsManager()


# Loop through all scraped movie/showings in json. Each item relates to a single cinema on a single day,and will contain one movie, and one or more showings for that movie
for item in data:
    # Using dummy cinema ID for now
    cinema_id = "P8110"
    # Process movie
    movie_man.process_movie(item)
    # Process showing
    show_man.process_showing(item, cinema_id)
    # break

# print(len(movie_man.new_movies))
# print(show_man.new_showings)
# pprint(show_man.current_showings)
# break
movie_man.add_new_movies_to_database()
show_man.add_new_showings_to_database()

# print(f"Total new movies added: {len(movie_man.new_movies)}")

# all_keys = sorted(movie_man.current_movie_ids)

# # for item in all_movies:
# #     print(item, all_movies[item].original_title)

# print(f"All movie_ids: {all_keys}")
