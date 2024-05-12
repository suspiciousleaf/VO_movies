import json
from pprint import pprint
import datetime
import time

import requests
from tqdm import tqdm

from creds import *
from cinema import CinemaManager
from showing import ShowingsManager
from movie import MovieManager

cinema_man = CinemaManager()
show_man = ShowingsManager()
movie_man = MovieManager()


class Scraper:
    def __init__(
        self, session: requests.Session, cinema_id: str, start_day: int, end_day: int
    ) -> None:
        """
        Initialize a Scraper object.

        Args:
            session(Session): Session object
            cinema_id (str): The ID of the cinema to scrape.
            start_day (int): The starting day for scraping. Today is day 0.
            end_day (int): The ending day for scraping.
        """
        self.session = session
        self.cinema_id = cinema_id
        self.target_urls = self.create_url_list(start_day, end_day)
        self.raw_json_data = []
        try:
            self.scrape_urls()
        except Exception as e:
            print(f"Scraper {self.cinema_id} failed: {e}")

    def create_url_list(self, start_day: int, end_day: int):
        """
        Return a list of all URLs to be scraped for this cinema.

        Args:
            start_day (int): The starting day for scraping.
            end_day (int): The ending day for scraping.

        Returns:
            list: List of URLs.
        """
        return [
            f"{base_prefix}{self.cinema_id}/d-{i}/" for i in range(start_day, end_day)
        ]

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
                "x-api-key": scraping_ant_api_key,
                "proxy_country": "FR",
                "browser": "false",
            }

            try:
                response = self.session.post(base_url, params=params, json=payload)
                response.raise_for_status()

                if response.status_code == 200:
                    data = response.json()
                    for showing in data["results"]:
                        if "ENGLISH" in showing["movie"]["languages"]:
                            if showing["showtimes"]["original"]:
                                self.raw_json_data.append(showing)

            except Exception as e:
                print(f"Error: {response.status_code=}, Exception: {e}")


class ScraperManager:
    def __init__(
        self,
        start_day,
        end_day,
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
        self.all_scraped_json_data = {}
        self.local_data_filename = local_data_filename
        if self.local_data_filename is not None and save_raw_json_data:
            raise Exception(
                "save_raw_json_data and local_data_filename are mutually exclusive: data can only be imported or exported, not both."
            )

        self.run_scrapers(start_day, end_day)
        # print(movie_man)
        movie_man.add_new_movies_to_database()
        # print(show_man)
        show_man.add_new_showings_to_database()
        print(movie_man)
        print(show_man)

        if save_raw_json_data:
            self.save_raw_data()

    def run_scrapers(self, start_day, end_day):
        """
        Run all scrapers for specified days and process the data.

        Args:
            start_day (int): The starting day for scraping. Today is day 0.
            end_day (int): The ending day for scraping.
        """
        if self.local_data_filename is None:
            with requests.Session() as session:
                for cinema in tqdm(cinema_man.cinema_ids, unit="Cinema"):
                    scraper = Scraper(session, cinema, start_day, end_day)
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

    @staticmethod
    def process_data(cinema, data):
        for showing in data:
            try:
                # Process movie
                movie_man.process_movie(showing)
                # Process showing
                show_man.process_showing(showing, cinema)
            except Exception as e:
                print(f"Movie could not be processed: {e}")

    def save_raw_data(self):
        """Save raw JSON data to a file."""
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"raw_data_{formatted_time}.json"

        with open(f"raw_data/{file_name}", "w", encoding="utf8") as f:
            json.dump(self.all_scraped_json_data, f, ensure_ascii=False)


if __name__ == "__main__":
    t0 = time.perf_counter()
    scraper_man = ScraperManager(
        1, 2, local_data_filename="raw_data_2024-05-12_16-08-45.json"
    )

    print(f"Time taken: {time.perf_counter() - t0:.2f}s")
