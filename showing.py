from datetime import datetime
from db_utilities import connect_to_database


class Showing:
    #! Create method to return something that can be added to database
    def __init__(
        self,
        movie_id: str,
        cinema_id: str,
        start_time: datetime,
    ):
        self.movie_id = movie_id
        self.start_time = start_time
        self.cinema_id = cinema_id


class ShowingsManager:
    def __init__(self):
        self.current_showings = set(self.retrieve_showings())
        self.new_showings = []

    @connect_to_database
    def retrieve_showings(self, db, cursor):
        try:
            table_name = "showtimes"
            query = f"SELECT movie_id, cinema_id, start_time FROM {table_name};"
            cursor.execute(query)
            results = cursor.fetchall()

            return results

        except Exception as e:
            print(f"ShowingsManager.retrieve_showings: An error occurred: {str(e)}")

    def create_showing(self, item, cinema_id):
        #! Find a way to pass cinema_id in from scraper - data not present in json. Could get by looping over each cinema, or maybe from url in response object
        if item["showtimes"]["original"]:
            for showing in item["showtimes"]["original"]:
                try:
                    movie_id = item["movie"]["id"]
                    date_str = showing["startsAt"]
                    start_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")

                    if (movie_id, cinema_id, start_time) in self.current_showings:
                        continue
                    else:
                        new_showing = Showing(movie_id, cinema_id, start_time)
                        self.new_showings.append(new_showing)
                        self.current_showings.add((movie_id, cinema_id, start_time))
                except:
                    continue


# show_man = ShowingsManager()
# print(show_man.current_showings)

#! Add functions to retrieve showings, compare newly scraped showings to those from database, and add new ones
#! Maybe add cinema manager to retrieve cinemas from database for front end

#! Method to add new_showings to database, same for new_movies
