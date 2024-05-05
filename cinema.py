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
        """
        Initialize a Cinema object.

        Args:
            cinema_id (str): The ID of the cinema.
            name (str): The name of the cinema.
            address (str): The address of the cinema.
            info (str): Additional information about the cinema.
            gps_raw (str): The GPS coordinates of the cinema in raw format.
            town (str): The town where the cinema is located.
        """
        self.cinema_id = cinema_id
        self.name = name
        self.address = address
        self.info = info
        self.gps = self.parse_gps(gps_raw)
        self.town = town

    def parse_gps(self, gps_raw: str | None) -> list[float] | None:
        """
        Parse the GPS coordinates from raw format to a more readable format.
        e.g. 'POINT(42.965081 1.607716)' from database becomes [42.965081 1.607716]

        Args:
            gps_raw (str | None): The GPS coordinates in raw format.

        Returns:
            list[float] | None: The parsed GPS coordinates or None if input is None.
        """

        gps = None
        if isinstance(gps_raw, str):
            gps = [
                float(coord)
                for coord in (gps_raw.replace("POINT(", "").replace(")", "").split(" "))
            ]
        return gps or gps_raw

    def __str__(self):
        """
        Return a string representation of the Cinema object.
        """
        return f"\nCinema details: \nID: {self.cinema_id}\nName: {self.name}\nTown: {self.town}\nAdditional info: {self.info}\nGPS coordinates: {self.gps}\nAddress: {self.address}"


class CinemaManager:
    """To access `cinema_id`s, iterate over the `CinemaManager` class instance"""

    def __init__(self):
        """Initialize a CinemaManager object."""
        self.cinemas = self.retrieve_cinemas()
        self.cinema_ids = [cinema.cinema_id for cinema in self.cinemas]

    @staticmethod
    @connect_to_database
    def retrieve_cinemas(db, cursor) -> list[str]:
        """
        Retrieve cinema information for all cinemas in the database.

        Returns:
            list[Cinema]: List of Cinema objects.
        """
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
        """
        Return a string representation of the CinemaManager object showing how many cinemas it contains.
        """
        return f"Cinema Manager Info:\nNumber of cinemas: {len(self.cinemas)}"
