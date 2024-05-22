from os import getenv
import json
import datetime
from logging import Logger

from dotenv import load_dotenv
import requests
from tqdm import tqdm

from cinema import CinemaManager
from showing import ShowingsManager
from movie import MovieManager

# take environment variables from .env
load_dotenv()

# Read environment variables
SCRAPING_ANT_API_KEY = getenv("scraping_ant_api_key")
BASE_PREFIX = getenv("base_prefix")
PAYLOAD = json.loads(getenv("payload"))


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
        url_list = [
            f"{BASE_PREFIX}{self.cinema_id}/d-{i}/" for i in range(start_day, end_day)
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

            except Exception:
                self.logger.error(
                    f"Request failed: {response.status_code=}", exc_info=True
                )


class ScraperManager:
    def __init__(
        self,
        start_day,
        end_day,
        logger: Logger,
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
        self.cinema_man = CinemaManager(logger)
        self.show_man = ShowingsManager(logger)
        self.movie_man = MovieManager(logger)

        logger.debug(
            "ScraperManager initialized successfully, checking new movie & showing info."
        )
        self.run_scrapers()
        self.movie_man.add_new_movies_to_database()
        self.show_man.add_new_showings_to_database()
        logger.info(self.movie_man)
        logger.info(self.show_man)

        if save_raw_json_data:
            self.save_raw_data()

    def run_scrapers(self):
        """
        Run all scrapers for specified days and process the data.

        """
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

    def process_data(self, cinema, data):
        for showing in data:
            try:
                # Process movie
                self.movie_man.process_movie(showing)
                # Process showing
                self.show_man.process_showing(showing, cinema)
            except Exception as e:
                self.logger.error(f"Unable to process data: {e}")  # , exc_info=True)

    def save_raw_data(self):
        """Save raw JSON data to a file."""
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"raw_data_{formatted_time}.json"
        self.logger.info(f"Saving raw scraped json data to {file_name}")

        with open(f"raw_data/{file_name}", "w", encoding="utf8") as f:
            json.dump(self.all_scraped_json_data, f, ensure_ascii=False)


class ScraperManagerInitializationError(Exception):
    """Exception to be raised when the scraper is required to load local data, and save data locally, in the same run"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
