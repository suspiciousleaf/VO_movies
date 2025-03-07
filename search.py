import time

from logging import Logger
from creds import DATA_REFRESH_AGE

from db_utilities import connect_to_database, DatabaseConnectionError


class Search:
    """
    A class for searching showtimes in the database.

    Attributes:
    results (list): A list to store the search results.
    """

    def __init__(self, logger: Logger):
        """Initialize the Search object."""
        self.logger = logger
        self.data: list | None = None
        self.time_at_data_refresh: float = 0.0
        self.max_data_age = DATA_REFRESH_AGE
        try:
            self.data = self.refresh_data()
        except DatabaseConnectionError as e:
            self.logger.error(f"DatabaseConnectionError: {e}")

    def get_movies(self) -> dict:
        """
        Perform a search for movies.

        Returns:
        list: A list of dictionaries containing search results.
        """
        data_source = "cache"
        data_age = time.time() - self.time_at_data_refresh
        if not self.data or data_age > self.max_data_age:
            self.data = self.refresh_data()
            data_source = "database"

        #! Uncomment to save json locally
        # import json
        # from datetime import date

        # def custom_serializer(obj):
        #     if isinstance(obj, date):  # Check if obj is a date
        #         return obj.isoformat()  # Convert to string (e.g., "2025-03-01")
        #     raise TypeError(
        #         f"Object of type {obj.__class__.__name__} is not JSON serializable"
        #     )

        # with open("test.json", "w", encoding="utf8") as f:
        #     json.dump(self.data, f, default=custom_serializer)
        self.logger.info(f"Search.get_movies() sourced data from {data_source}")
        return self.data.get("movies", {})

    def get_showings(self) -> list[dict]:
        """
        Perform a search for movies.

        Returns:
        list: A list of dictionaries containing search results.
        """
        data_source = "cache"
        data_age = time.time() - self.time_at_data_refresh
        if not self.data or data_age > self.max_data_age:
            self.data = self.refresh_data()
            data_source = "database"

        self.logger.info(f"Search.get_showings() sourced data from {data_source}")
        return self.data.get("showings", {})

    @connect_to_database
    def refresh_data(self, db, cursor) -> list:
        """
        Update the cached data from the database

        Args:
        db: Database connection object.
        cursor: Database cursor object. This is passed by the decorator, but overridden in this method to return as dictionary.
        """

        try:
            cursor = db.cursor(dictionary=True)
            columns_required = "movies.movie_id AS movie_id, start_time, original_title, runtime, synopsis, cast, genres, release_date, rating_imdb, rating_rt, rating_meta, imdb_url, poster_hi_res, poster_lo_res, name AS cinema_name, town AS cinema_town, showtimes.cinema_id"
            search_query = f"SELECT {columns_required} FROM showtimes LEFT JOIN movies ON showtimes.movie_id = movies.movie_id LEFT JOIN cinemas ON showtimes.cinema_id = cinemas.cinema_id WHERE start_time > DATE(NOW()) ORDER BY start_time ASC"

            cursor.execute(search_query)

            results = cursor.fetchall()
            if results:
                for result in results:
                    d_t = result["start_time"]
                    result["start_time"] = {
                        "time": d_t.strftime("%#H:%M"),
                        "date": f"{d_t.strftime('%#d')} {d_t.strftime('%B')}",
                        "year": d_t.strftime("%Y"),
                    }
            data = self._process_data_from_db(results)
            self.time_at_data_refresh = time.time()
            self.logger.info(
                f"Data refreshed at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
            )
            self.time_at_data_refresh = time.time()
            return data
        except Exception as e:
            self.logger.error(f"Search.refresh_data() failed: {e}", exc_info=True)

    @staticmethod
    def date_with_suffix(n: str) -> str:
        """Function to get the date suffix"""
        n = int(n)
        if 11 <= n % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def _process_data_from_db(self, showings):
        processed_data = {"movies": {}, "showings": []}
        movie_names = set()
        showings_set = set()

        for showing in showings:
            try:
                if showing.get("original_title") not in movie_names:
                    movie_names.add(showing.get("original_title"))
                    processed_data["movies"][showing.get("original_title")] = {
                        # movie_id is needed to update ratings, not for main results
                        "movie_id": showing.get("movie_id"),
                        "runtime": showing.get("runtime"),
                        "synopsis": showing.get("synopsis"),
                        "cast": showing.get("cast"),
                        "genres": showing.get("genres"),
                        "release_date": showing.get("release_date"),
                        "rating_imdb": showing.get("rating_imdb") / 10
                        if showing.get("rating_imdb")
                        else None,
                        "rating_rt": showing.get("rating_rt"),
                        "rating_meta": showing.get("rating_meta"),
                        "imdb_url": showing.get("imdb_url"),
                        "poster_hi_res": showing.get("poster_hi_res"),
                        "poster_lo_res": showing.get("poster_lo_res"),
                    }
                cinema = f"{showing['cinema_name']},{showing['cinema_town']}"
                original_title = showing.get("original_title")
                start_time = f"{showing.get('start_time', {}).get('time')},{showing.get('start_time', {}).get('date')},{showing.get('start_time', {}).get('year')}"
                showing_string = f"{start_time},{original_title},{cinema}"

                if showing_string not in showings_set:
                    showings_set.add(showing_string)
                    processed_data["showings"].append(
                        {
                            "cinema": cinema,
                            "original_title": original_title,
                            "start_time": showing.get("start_time"),
                        }
                    )
            except Exception as e:
                self.logger.warning(f"Error processing movie: {e}: {showing}")
        return processed_data


if __name__ == "__main__":
    # Test search behaviour
    from logging import getLogger
    from logs.setup_logger import setup_logging

    logger = getLogger(__name__)
    setup_logging()
    search = Search(logger)
    # while True:
    #     x = input("Enter anything to continue")
    #     t0 = time.perf_counter()
    results = search.search()
    # t1 = time.perf_counter() - t0
    # logger.info(f"Number of results: {len(results)}")
    # if results:
    #     logger.info(
    #         f"{results['data_source']}, {results['data_age']:.2f} s, took {t1 * 1000:.2f} ms"
    #     )
