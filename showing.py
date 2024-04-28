from db_utilities import connect_to_database


class Showing:
    def __init__(
        self,
        allocine_id: str = "",
        start_time: str = "",
        cinema_id: str = "",
    ):
        self.allocine_id = allocine_id
        self.start_time = start_time
        self.cinema_id = cinema_id


class ShowingsManager:
    def __init__(self):
        self.showings = self.retrieve_showings()

    @connect_to_database
    def retrieve_showings(db, cursor):
        try:
            cursor = db.cursor(dictionary=True)

            table_name = "showtimes"

            query = f"SELECT movie_id, cinema_id, start_time FROM {table_name};"

            cursor.execute(query)

            results = cursor.fetchall()

            return results

        except Exception as e:
            print(f"An error occurred: {str(e)}")
