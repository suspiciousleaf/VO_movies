import time
from threading import Lock

from logging import Logger
from creds import DATA_REFRESH_AGE

from db_utilities import connect_to_database, DatabaseConnectionError


class Search:
    """
    A class that manages cached access to movie and showing data from the database.

    This class implements a thread-safe caching mechanism that reduces database load
    by storing movie and showing data in memory and refreshing it only when necessary.

    Attributes:
        logger (Logger): Logger instance for recording operations and errors.
        data (dict): Cached data containing movies and showings.
        time_at_data_refresh (float): Timestamp of the last data refresh.
        max_data_age (int): Maximum age of cached data in seconds before refresh.
        _refresh_lock (Lock): Thread lock to prevent concurrent database refreshes.
    """

    def __init__(self, logger: Logger):
        """
        Initialize the Search object with empty cache and refresh settings.

        Args:
            logger (Logger): Logger instance for recording operations and errors.

        Raises:
            DatabaseConnectionError: If initial database connection fails.
        """
        self.logger: Logger = logger
        self.data: dict = {}
        self.time_at_data_refresh: float = 0.0
        self.max_data_age: int = DATA_REFRESH_AGE
        self._refresh_lock: Lock = Lock()
        try:
            self.data = self._refresh_data()
        except DatabaseConnectionError as e:
            self.logger.error(f"DatabaseConnectionError: {e}")

    def get_movies(self, force_refresh=False) -> dict:
        """
        Retrieve movie data from cache or refresh from database if needed.

        The method checks if the cached data is stale based on age or if a refresh
        is explicitly requested. Uses thread-safe mechanisms to prevent multiple
        concurrent refreshes.

        Args:
            force_refresh (bool, optional): Force a data refresh regardless of cache age.
                Defaults to False.

        Returns:
            dict: Dictionary mapping movie titles to their details. Empty dict if no data.
        """
        data_source = "cache"
        current_data_age = time.time() - self.time_at_data_refresh
        # Check conditions to refresh cache. Empty cache, force_refresh, or stale data
        if not self.data or force_refresh or current_data_age > self.max_data_age:
            with self._refresh_lock:
                # Check conditions again after aquiring lock to prevent double refreshes.
                current_data_age = time.time() - self.time_at_data_refresh
                if (
                    not self.data
                    or force_refresh
                    or current_data_age > self.max_data_age
                ):
                    self.data = self._refresh_data()
                    data_source = "database"

        self.logger.info(
            f"Search.get_movies() sourced data from {data_source}, current_data_age={round(current_data_age, 0)}s, {force_refresh=}"
        )
        return self.data.get("movies", {})

    def get_showings(self, force_refresh=False) -> list[dict]:
        """
        Retrieve showing data from cache or refresh from database if needed.

        The method checks if the cached data is stale based on age or if a refresh
        is explicitly requested. Uses thread-safe mechanisms to prevent multiple
        concurrent refreshes.

        Args:
            force_refresh (bool, optional): Force a data refresh regardless of cache age.
                Defaults to False.

        Returns:
            list[dict]: List of showing dictionaries with cinema, title and time information.
                Empty list if no data.
        """
        data_source = "cache"
        current_data_age = time.time() - self.time_at_data_refresh
        # Check conditions to refresh cache. Empty cache, force_refresh, or stale data
        if not self.data or force_refresh or current_data_age > self.max_data_age:
            with self._refresh_lock:
                # Check conditions again after aquiring lock to prevent double refreshes.
                current_data_age = time.time() - self.time_at_data_refresh
                if (
                    not self.data
                    or force_refresh
                    or current_data_age > self.max_data_age
                ):
                    self.data = self._refresh_data()
                    data_source = "database"

        self.logger.info(
            f"Search.get_showings() sourced data from {data_source}, current_data_age={round(current_data_age, 0)}s, {force_refresh=}"
        )
        return self.data.get("showings", [])

    @connect_to_database
    def _refresh_data(self, db, cursor) -> dict:
        """
        Fetch fresh data from the database and update the cache.

        This method is decorated with @connect_to_database which handles the database
        connection. It queries upcoming showtimes and related movie information,
        formats the data, and updates the cache timestamp.

        Args:
            db: Database connection object (provided by decorator).
            cursor: Database cursor object (provided by decorator).

        Returns:
            dict: Refreshed data dictionary with 'movies' and 'showings' keys.
                Returns empty structures if errors occur.
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
            data: dict = self._process_data_from_db(results)
            self.logger.info(
                f"Data refreshed at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
            )
            self.time_at_data_refresh = time.time()
            return data
        except Exception as e:
            self.logger.error(f"Search.refresh_data() failed: {e}", exc_info=True)
            return {"movies": {}, "showings": []}

    @staticmethod
    def date_with_suffix(n: str) -> str:
        """
        Add an appropriate ordinal suffix to a numeric date.

        Args:
            n (str): Numeric day of the month as string.

        Returns:
            str: Date with appropriate suffix (e.g., "1st", "2nd", "3rd", "4th").
        """
        n = int(n)
        if 11 <= n % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def _process_data_from_db(self, showings: list[dict]) -> dict:
        """
        Process raw database results into structured cache format.

        This method separates movie details from showing information and
        deduplicates entries to create an efficient cache structure.

        Args:
            showings (list[dict]): Raw showing data from database query.

        Returns:
            dict: Processed data with 'movies' dict and 'showings' list.
        """
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
    results = search.get_movies()
    # t1 = time.perf_counter() - t0
    # logger.info(f"Number of results: {len(results)}")
    # if results:
    #     logger.info(
    #         f"{results['data_source']}, {results['current_data_age']:.2f} s, took {t1 * 1000:.2f} ms"
    #     )
