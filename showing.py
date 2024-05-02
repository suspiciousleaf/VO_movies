from datetime import datetime
import hashlib
from pprint import pprint

from db_utilities import connect_to_database

TABLE_NAME = "showtimes"


class Showing:

    @staticmethod
    def get_columns() -> tuple[str]:
        """Returns a tuple of the database column names to be written to"""
        return ("movie_id", "cinema_id", "start_time", "hash_id")

    def __init__(
        self,
        movie_id: str,
        cinema_id: str,
        start_time: datetime,
    ) -> None:
        self.movie_id = movie_id
        self.cinema_id = cinema_id
        self.start_time = start_time
        self.hash_id = self.calculate_hash(
            self.movie_id, self.cinema_id, self.start_time
        )

    # Hash function to create a single data point for each showing that can be compared with newly scraped showings, to identify showings not yet in the database. @staticmethod used as it does not require 'self' to be passed.
    @staticmethod
    def calculate_hash(movie_id: str, cinema_id: str, start_time: datetime) -> str:
        # Create a single string
        data = f"{movie_id}{cinema_id}{start_time}"
        # Calculate the SHA-256 hash
        hash_value = hashlib.sha256(data.encode()).hexdigest()

        return hash_value

    def __str__(self) -> str:
        return f"\nMovie ID: {self.movie_id} \nCinema ID: {self.cinema_id} \nStart Time: {self.start_time} \nHash ID: {self.hash_id}"

    def __repr__(self) -> str:
        return f"Showing({self.movie_id}, {self.cinema_id}, {self.start_time})"


class ShowingsManager:
    def __init__(self) -> None:
        self.current_showings = set(self.retrieve_showings())
        self.new_showings = []

    @staticmethod
    @connect_to_database
    def retrieve_showings(db, cursor) -> list[tuple[str]]:
        """Retrieve hash_id values for all showings in database"""
        try:
            query = f"SELECT hash_id FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            return [result[0] for result in results]

        except Exception as e:
            print(f"ShowingsManager.retrieve_showings: An error occurred: {str(e)}")

    def showing_already_in_database(self, hash_id: str) -> bool:
        """Check if hash_id is recognised. Return False if showing not in database. Convert to tuple to match data type from database"""
        return hash_id in self.current_showings

    def process_showing(self, item: dict, cinema_id: str) -> None:
        """Create Showing object(s) for each movie & showing object in scraped json, check if showing is already in database, and if not add to new_showings list for batch addition"""

        if item["showtimes"]["original"]:
            for showing in item["showtimes"]["original"]:
                try:
                    # Identify valuesfor new showing
                    movie_id = item["movie"]["id"]
                    date_str = showing["startsAt"]
                    start_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
                    # Create new Showing object, to create hash_id for comparison with current showings
                    new_showing = Showing(movie_id, cinema_id, start_time)
                    # Check if new showing is already in database by comparing hash_id, if not add to list to new showings to be added to database
                    if not self.showing_already_in_database(new_showing.hash_id):
                        self.add_new_showing(new_showing)
                except:
                    continue

    def add_new_showing(self, new_showing: Showing) -> None:
        """Add new showing to new_showings list to be added to database, and add hash_id to set"""
        self.new_showings.append(new_showing)
        self.current_showings.add((new_showing.hash_id,))

    @connect_to_database
    def add_new_showings_to_database(self, db=None, cursor=None) -> None:
        if self.new_showings:
            """Run this to add all new showings stored in self.new_showings to database"""

            # List of dicts of values for each new showing to be inserted into {TABLE_NAME} table
            showing_values_list = [showing.__dict__ for showing in self.new_showings]

            # All columns to be inserted into {TABLE_NAME} table
            columns = Showing.get_columns()
            # Create placeholders for values to be inserted
            placeholders = ", ".join(f"%({key})s" for key in columns)
            # Create INSERT query
            insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders});"
            # Execute above query to insert new showings into database
            cursor.executemany(insert_query, showing_values_list)
            # Commit changes to database
            db.commit()

    def __str__(self):
        if self.new_showings:
            return f"{len(self.new_showings)} new showings found:\n" + "\n".join(
                str(show) for show in self.new_showings
            )
        else:
            return "No new showings"
