from pprint import pprint
from db_utilities import connect_to_database

from geopy.adapters import AioHTTPAdapter
from geopy.geocoders import Nominatim
from geopy.location import Location


TABLE_NAME = "cinemas"


class Cinema:
    def __init__(
        self,
        cinema_id: str,
        name: str,
        address: str,
        info: str,
        gps: str | list[float],
        town: str,
    ) -> None:
        """
        Initialize a Cinema object.

        Args:
            cinema_id (str): The ID of the cinema.
            name (str): The name of the cinema.
            address (str): The address of the cinema.
            info (str): Additional information about the cinema.
            gps (str): The GPS coordinates of the cinema in raw format.
            town (str): The town where the cinema is located.
        """
        self.cinema_id = cinema_id
        self.name = name
        self.address = address
        self.info = info
        self.gps = self.parse_gps(gps)
        self.town = town

    def parse_gps(self, gps: str | list[float] | None) -> list[float] | None:
        """
        Parse the GPS coordinates from raw database format to a more readable format.
        e.g. 'POINT(42.965081 1.607716)' from database becomes [42.965081 1.607716]
        If provided in list form for insertion into database, will be left untouched.

        Args:
            gps (str | list[float] | None): The GPS coordinates in raw format.

        Returns:
            list[float] | None: The parsed GPS coordinates or None if input is None.
        """

        # gps = None
        if isinstance(gps, str):
            try:
                gps = [
                    float(coord)
                    for coord in (gps.replace("POINT(", "").replace(")", "").split(" "))
                ]
            except:
                gps = None
        return gps or None

    @connect_to_database
    def add_to_database(self, db, cursor):
        """Adds cinema object to the database if not already present"""
        try:
            columns = list(self.__dict__.keys())
            values = self.__dict__
            gps = values.get("gps")

            # If GPS details are provided, extracts lat and lon to be added via placeholder, and removes "gps" key so it can be placed in the correct index for addition.
            if isinstance(gps, list):
                values["lat"] = gps[0]
                values["lon"] = gps[1]
                values.pop("gps")
                columns.remove("gps")
                placeholders = ", ".join(f"%({key})s" for key in columns)
                # Create the GPS string and places it at the first index position.
                gps_string = "ST_GeomFromText('POINT(%(lat)s %(lon)s)', 4326)"
                insert_query = f"INSERT INTO {TABLE_NAME} (gps, {', '.join(columns)}) VALUES ({gps_string}, {placeholders});"
            else:
                placeholders = ", ".join(f"%({key})s" for key in columns)
                insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders});"

            cursor.execute(insert_query, values)
            db.commit()
            return {"ok": True, "info": None}

        except Exception as e:
            print(f"CinemaManager.add_to_database: An error occurred: {str(e)}")
            return {
                "ok": False,
                "info": f"cinema.add_to_database: An error occurred: {e}",
            }

    def __str__(self):
        """
        Return a string representation of the Cinema object.
        """
        return f"\nID: {self.cinema_id}\nName: {self.name}\nTown: {self.town}\nAdditional info: {self.info}\nAddress: {self.address}\nGPS coordinates: {self.gps}"


class CinemaManager:
    """To access `cinema_id`s, iterate over the `CinemaManager` class instance"""

    def __init__(self, logger):
        """Initialize a CinemaManager object."""
        self.logger = logger
        self.cinemas = self.retrieve_cinemas(logger=logger)
        self.cinema_ids = set(cinema.cinema_id for cinema in self.cinemas)

    @staticmethod
    @connect_to_database
    def retrieve_cinemas(db, cursor, logger) -> list[str]:
        """
        Retrieve cinema information for all cinemas in the database.

        Returns:
            list[Cinema]: List of Cinema objects.
        """
        try:
            logger.debug(f"Retrieving cinemas from databse")
            cursor = db.cursor(dictionary=True)
            query = f"SELECT cinema_id, name, address, info, ST_AsText(gps) AS gps, town FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            cinema_objects = [Cinema(**cinema) for cinema in results]

            return cinema_objects

        except Exception as e:
            logger.critical(
                f"CinemaManager.retrieve_cinemas: An error occurred: {str(e)}",
                exc_info=True,
            )
            raise e

    @staticmethod
    async def get_gps(cinema: dict) -> Location | None:
        """Returns GPS coordinates of cinema location in France."""
        address = cinema.get("address") or ""
        name = cinema.get("name") or ""
        town = cinema.get("town") or ""
        geolocator = Nominatim(user_agent="cinema-app")
        async with Nominatim(
            user_agent="cinema-app", adapter_factory=AioHTTPAdapter
        ) as geolocator:
            location = None
            searches = [address, f"{name} {town}", town]

            # Tries first using the full address, then using the cinema name and town, and finally just with the town. Decreasing accuracy but higher chance of success with each iteration.
            for search in searches:
                if search and location is None:
                    try:
                        location = await geolocator.geocode(f"{search}, France")
                    except:
                        pass
            if isinstance(location, Location):
                location = [location.latitude, location.longitude]

            return location

    async def add_cinema_to_database(self, cinema: dict):
        """Creates a new Cinema object and adds it to the database, so that the cinema will be scraped in the future.
        New cinema details to be provided as a dict with keys matching the database columns:
        {"cinema_id":str,
        "name":str | None,
        "address":str | None,
        "info":str | None,
        "gps": list[float] | None,
        "town":str | None}

        Note: "cinema_id" is obligatory, "gps" will attempt to be found if not provided.
        """
        if cinema.get("cinema_id") in self.cinema_ids:
            return {"ok": False, "code": 409, "info": "Cinema ID already in database"}
        else:
            try:
                response = None
                # If gps is not provided, or is in incorrect format, attempt to find correct gps coordinates
                if cinema.get("gps") is None or not all(
                    isinstance(x, float) for x in cinema.get("gps")
                ):
                    cinema["gps"] = await self.get_gps(cinema)
                # Create new Cinema object and add it to the database
                new_cinema = Cinema(**cinema)
                # print(new_cinema)
                response = new_cinema.add_to_database()
                if response["ok"]:
                    self.cinema_ids.add(new_cinema.cinema_id)
                    return {"ok": True, "code": 201, "info": "Cinema added to database"}
                else:
                    return response

            except Exception as e:
                resp_dict = {"ok": False, "code": 400, "info": [f"Bad request: {e}"]}
                if response is not None:
                    resp_dict["info"].append(response.get("info"))
                return resp_dict

    @connect_to_database
    def delete_cinema(self, db, cursor, cinema_id: dict):
        """Delete cinema from database using cinema_id"""
        if cinema_id["cinema_id"] not in self.cinema_ids:
            return {"ok": False, "code": 409, "info": "Cinema ID not in database"}
        else:
            try:
                delete_query = f"DELETE FROM {TABLE_NAME} WHERE cinema_id = %s;"
                cursor.execute(delete_query, (cinema_id["cinema_id"],))
                db.commit()
                self.cinema_ids.remove(cinema_id["cinema_id"])
                return {"ok": True, "code": 200, "info": "Cinema removed from database"}

            except Exception as e:
                return {"ok": False, "code": 400, "info": f"Bad request: {e}"}

    def retrieve_cinema_info(self) -> str:
        """Return a string showing info for each cinema in the database"""
        cinemas_info = (
            "\n".join(str(cinema) for cinema in self.cinemas) + f"\n{str(self)}"
        )
        return cinemas_info

    def __str__(self):
        """
        Return a string representation of the CinemaManager object showing how many cinemas it contains.
        """
        return f"\nTotal cinemas: {len(self.cinemas)}"
