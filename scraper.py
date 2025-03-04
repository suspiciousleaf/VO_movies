import json
import datetime
from logging import Logger

import requests
from tqdm import tqdm

from cinema import CinemaManager
from showing import ShowingsManager
from movie import MovieManager
from search import Search
from db_utilities import connect_to_database
from creds import SCRAPING_ANT_API_KEY, BASE_PREFIX, PAYLOAD, OMDB_API_URL, OMDB_API_KEY


# Scraper class, instantiate once per cinema, scrapes the full date range and stores raw data to be processed.
class Scraper:
    def __init__(
        self,
        logger: Logger,
        session: requests.Session,
        cinema_id: str,
        start_day: int,
        end_day: int,
    ) -> None:
        """
        Initialize a Scraper object.

        Args:
            logger (Logger): Logger object.
            session(Session): Session object
            cinema_id (str): The ID of the cinema to scrape.
            start_day (int): The starting day for scraping. Today is day 0.
            end_day (int): The ending day for scraping.
        """
        self.logger = logger
        self.session = session
        self.cinema_id = cinema_id
        self.target_urls = self.create_url_list(start_day, end_day)
        self.raw_json_data = []
        try:
            self.scrape_urls()
        except Exception:
            self.logger.error(
                f"Scraper failed for cinema_id: {self.cinema_id}", exc_info=True
            )

    def create_url_list(self, start_day: int, end_day: int):
        """
        Return a list of all URLs to be scraped for this cinema.

        Args:
            start_day (int): The starting day for scraping.
            end_day (int): The ending day for scraping.

        Returns:
            list: List of URLs.
        """
        today_date = datetime.date.today()
        url_list = [
            f"{BASE_PREFIX}{self.cinema_id}/d-{today_date + datetime.timedelta(days=i)}/"
            for i in range(start_day, end_day)
        ]
        self.logger.debug(
            f"Scraper.create_url_list() for {self.cinema_id=} ran successfully"
        )
        return url_list

    def return_data(self):
        """
        Return all the scraped raw data.

        Returns:
            list: List of raw JSON data.
        """
        return self.raw_json_data

    def scrape_urls(self) -> list:
        """
        Run scraper on all target URLs and process responses.

        Returns:
            list: List of scraped data.
        """
        for target_url in self.target_urls:
            base_url = "https://api.scrapingant.com/v2/general"
            params = {
                "url": target_url,
                "x-api-key": SCRAPING_ANT_API_KEY,
                "proxy_country": "FR",
                "browser": "false",
            }

            try:
                response = self.session.post(base_url, params=params, json=PAYLOAD)
                response.raise_for_status()

                if response.status_code == 200:
                    data = response.json()
                    for showing in data["results"]:
                        if "ENGLISH" in showing["movie"]["languages"]:
                            if showing["showtimes"]["original"]:
                                self.raw_json_data.append(showing)

            except Exception as e:
                self.logger.error(
                    f"Request failed: {response.status_code=}, {target_url=}",
                    extra={
                        "extra_info": str(e).replace(
                            SCRAPING_ANT_API_KEY, "SCRAPING_ANT_API_KEY"
                        )
                    },
                )


# Instantiate to initialize scraping across the specified date range, will scrape the data for all cinemas, process the raw data, and add new data to database. Raw data can also be saved, or imported rather than scraping.
class ScraperManager:
    def __init__(
        self,
        logger: Logger,
        start_day: int = 0,
        end_day: int = 15,
        save_raw_json_data=False,
        local_data_filename: str | None = None,
    ):
        """
        Initialize a ScraperManager object.

        Args:
            start_day (int): The starting day for scraping. Today is day 0.
            end_day (int): The ending day for scraping.
            save_raw_json_data (bool, optional): Whether to save raw JSON data. Defaults to False.
        """
        self.start_day = start_day
        self.end_day = end_day
        self.logger = logger
        self.all_scraped_json_data = {}
        self.local_data_filename = local_data_filename
        if self.local_data_filename is not None and save_raw_json_data:
            error_message = "`save_raw_json_data` and `local_data_filename` are mutually exclusive: When instantiating a ScraperManager object, one or both arguments must be false or not provided"
            raise ScraperManagerInitializationError(error_message)

        logger.debug("Initializing  cinema, movie, and showing managers")
        try:
            self.cinema_man: CinemaManager = CinemaManager(logger)
            self.show_man: ShowingsManager = ShowingsManager(logger)
            self.movie_man: MovieManager = MovieManager(logger)
            self.search: Search = Search(logger)

            logger.debug(
                "ScraperManager initialized successfully, checking new movie & showing info."
            )
            self.run_scrapers()
            self.movie_man.add_new_movies_to_database()
            self.show_man.add_new_showings_to_database()
            logger.info(self.movie_man)
            logger.info(self.show_man)
            self.update_ratings()

            if save_raw_json_data:
                self._save_raw_data()
        except Exception as e:
            self.logger.error(f"Error running ScraperManager: {e}", exc_info=True)

    def run_scrapers(self):
        """
        Run all scrapers for specified days and process the data.

        """
        # If `local_data_filename` is provided, raw data will be imported and processed. If not provided, new raw data will be scraped and processed.
        try:
            if self.local_data_filename is None:
                with requests.Session() as session:
                    for cinema in tqdm(self.cinema_man.cinema_ids, unit="Cinema"):
                        scraper = Scraper(
                            logger=self.logger,
                            session=session,
                            cinema_id=cinema,
                            start_day=self.start_day,
                            end_day=self.end_day,
                        )
                        data = scraper.return_data()
                        self.all_scraped_json_data[cinema] = data
                        self.process_data(cinema, data)
            else:
                with open(
                    f"raw_data/{self.local_data_filename}", "r", encoding="utf8"
                ) as f:
                    local_data = json.load(f)
                for cinema, data in local_data.items():
                    self.process_data(cinema, data)
        except Exception as e:
            self.logger.error(f"Error running scrapers: {e}", exc_info=True)

    def process_data(self, cinema, data):
        for showing in data:
            try:
                # Process movie
                self.movie_man.process_movie(showing)
                # Process showing
                self.show_man.process_showing(showing, cinema)
            except Exception as e:
                self.logger.error(f"Unable to process data: {e}")

    @connect_to_database
    def update_ratings(self, db, cursor) -> None:
        """Update ratings in database for upcoming movies"""

        ratings_values_list = self._get_movies_for_ratings_update()
        if not ratings_values_list:
            self.logger.info("No movie ratings to update")
            return
        try:
            columns = ["rating_imdb", "rating_rt", "rating_meta"]
            TABLE_NAME = "movies"

            set_clause = ", ".join(f"{col} = %({col})s" for col in columns)
            update_query = f"""
                UPDATE {TABLE_NAME}
                SET {set_clause}
                WHERE movie_id = %(movie_id)s;
            """

            cursor.executemany(update_query, ratings_values_list)
            db.commit()

            self.logger.info(f"Ratings updated for {len(ratings_values_list)} movies")
        except Exception as e:
            self.logger.error(f"Error updating ratings: {e}", exc_info=True)

    def _get_movies_for_ratings_update(self):
        try:
            # Get a list of upcoming movies so we know which ones to update
            upcoming_movies = self.search.search().get("movies", [])

            # Filter the results to get just the details we need
            IMDB_IDS = [
                {
                    "movie_id": upcoming_movies.get(movie, {}).get("movie_id"),
                    "imdb_id": upcoming_movies.get(movie, {})
                    .get("imdb_url", "")
                    .split("/")[-1],
                }
                for movie in upcoming_movies
                if upcoming_movies.get(movie, {}).get("imdb_url", "")
            ]
        except Exception as e:
            self.logger.error(f"Unable to get movie_ids for ratings update: {e}")

        ratings_values_list = []
        try:
            with requests.Session() as session:
                for movie in IMDB_IDS:
                    try:
                        params = {
                            "apikey": OMDB_API_KEY,
                            "i": movie["imdb_id"],
                            "plot": "short",
                        }

                        response = session.get(url=OMDB_API_URL, params=params)
                        response.raise_for_status()

                        ratings = response.json().get("Ratings", {})

                        rating_imdb, rating_rt, rating_meta = None, None, None
                        for rating in ratings:
                            match rating["Source"]:
                                case "Internet Movie Database":
                                    if isinstance(rating["Value"], str):
                                        rating_imdb = int(
                                            float(rating["Value"].split("/")[0]) * 10
                                        )
                                case "Rotten Tomatoes":
                                    if isinstance(rating["Value"], str):
                                        rating_rt = int(
                                            rating["Value"].replace("%", "")
                                        )
                                case "Metacritic":
                                    if isinstance(rating["Value"], str):
                                        rating_meta = int(rating["Value"].split("/")[0])

                        ratings_values_list.append(
                            {
                                "movie_id": movie["movie_id"],
                                "rating_imdb": rating_imdb,
                                "rating_rt": rating_rt,
                                "rating_meta": rating_meta,
                            }
                        )
                    except requests.RequestException as e:
                        self.logger.error(
                            f"Failed to fetch ratings for {movie['imdb_id']}: {e}"
                        )
                        continue
        except Exception as e:
            self.logger.error(
                f"Error fetching movies for ratings update: {e}", exc_info=True
            )
            return []

        return ratings_values_list

    def _save_raw_data(self):
        """Save raw JSON data to a file."""
        try:
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"raw_data_{formatted_time}.json"
            self.logger.info(f"Saving raw scraped json data to {file_name}")

            with open(f"raw_data/{file_name}", "w", encoding="utf8") as f:
                json.dump(self.all_scraped_json_data, f, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving raw json data: {e}")


class ScraperManagerInitializationError(Exception):
    """Exception to be raised when the scraper is required to load local data, and save data locally, in the same run"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
