from pprint import pprint
from db_utilities import connect_to_database

TABLE_NAME = "cinemas"


class Cinema:
    def __init__(
        self,
        cinema_id: str,
        name: str,
        address: str,
        info: str,
        gps_raw: str,
        town: str,
    ) -> None:
        self.cinema_id = cinema_id
        self.name = name
        self.address = address
        self.info = info
        self.gps = self.parse_gps(gps_raw)
        self.town = town

    def parse_gps(self, gps_raw: str | None) -> list[float] | None:
        """This is to convert the output from the database to a more readable format.
        'POINT(42.965081 1.607716)' from database becomes [42.965081 1.607716]"""

        gps = None
        if isinstance(gps_raw, str):
            gps = [
                float(coord)
                for coord in (gps_raw.replace("POINT(", "").replace(")", "").split(" "))
            ]
        return gps or gps_raw

    def __str__(self):
        return f"\nCinema details: \nID: {self.cinema_id}\nName: {self.name}\nTown: {self.town}\nAdditional info: {self.info}\nGPS coordinates: {self.gps}\nAddress: {self.address}"


class CinemaManager:
    """To access `cinema_id`s, iterate over the `CinemaManager` class instance"""

    def __init__(self):
        self.cinemas = self.retrieve_cinemas()
        self.cinema_ids = [cinema.cinema_id for cinema in self.cinemas]

    @staticmethod
    @connect_to_database
    def retrieve_cinemas(db, cursor) -> list[str]:
        """Retrieve cinema information for all cinemas in database"""
        try:
            cursor = db.cursor(dictionary=True)
            query = f"SELECT cinema_id, name, address, info, ST_AsText(gps) AS gps_raw, town FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            cinema_objects = [Cinema(**cinema) for cinema in results]

            return cinema_objects

        except Exception as e:
            print(f"ShowingsManager.retrieve_showings: An error occurred: {str(e)}")

    def __str__(self):
        return f"Cinema Manager Info:\nNumber of cinemas: {len(self.cinemas)}"
