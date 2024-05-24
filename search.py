import datetime
from logging import Logger

from db_utilities import connect_to_database


class Search:
    """
    A class for searching showtimes in the database.

    Attributes:
    results (list): A list to store the search results.
    """

    def __init__(self, logger: Logger):
        """Initialize the Search object."""
        self.logger = logger
        self.results = []

    def search(self, towns: list[str] | None = None):
        """
        Perform a search for showtimes based on specified towns.

        Args:
        towns (list[str] | None, optional): A list of town names to filter the search. Defaults to None. Case and accent insensitive.

        Returns:
        list: A list of dictionaries containing search results.
        """
        self.results = self.search_showings(towns=towns)
        return self.results

    @connect_to_database
    def search_showings(self, db, cursor, towns: list[str] | None = None):
        """
        Execute the SQL query to search for showtimes in the database.

        Args:
        db: Database connection object.
        cursor: Database cursor object. This is passed by the decorator, but overridden in this method to return as dictionary.
        towns (list[str] | None, optional): A list of town names to filter the search. Defaults to None.

        Returns:
        list: A list of dictionaries containing search results.
        """

        try:
            cursor = db.cursor(dictionary=True)
            columns_required = "start_time, original_title, french_title, runtime, synopsis, cast, languages, genres, release_date, rating, imdb_url, origin_country, poster_hi_res, poster_lo_res, tagline, name AS cinema_name, town AS cinema_town, address AS cinema_address"
            search_query = f"SELECT {columns_required} FROM showtimes LEFT JOIN movies ON showtimes.movie_id = movies.movie_id LEFT JOIN cinemas ON showtimes.cinema_id = cinemas.cinema_id WHERE start_time > DATE(NOW())"

            if towns:
                try:
                    assert all(isinstance(town, str) for town in towns)
                except:
                    raise ValueError(
                        f"All 'town' values must be strings, towns={towns}"
                    )

                placeholders = ", ".join(f"%s" for _ in towns)
                search_query += f" AND town IN ({placeholders})"
                cursor.execute(search_query, towns)
            else:
                cursor.execute(search_query)

            results = cursor.fetchall()
            if results:
                for result in results:
                    d_t = result["start_time"]
                    result["start_time"] = {
                        "time": d_t.strftime("%#H:%M"),
                        "date": f"{self.date_with_suffix(d_t.strftime('%#d'))} {d_t.strftime('%B')}",
                    }
            return results

        except Exception as e:
            self.logger.error(f"Search.search_showings() failed: {e}")
            return []

    @staticmethod
    def date_with_suffix(n: str) -> str:
        """Function to get the date suffix"""
        n = int(n)
        if 11 <= n % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"


if __name__ == "__main__":
    # Test search behaviour
    from logging import getLogger
    from logs.setup_logger import setup_logging

    logger = getLogger(__name__)
    setup_logging()
    search = Search(logger)
    results = search.search()
    logger.info(f"Number of results: {len(results)}")
    if results:
        logger.info(results[0])
