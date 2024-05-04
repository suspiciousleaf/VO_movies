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
    def __init__(self, cinema_id: str, start_day: int, end_day: int) -> None:
        self.cinema_id = cinema_id
        self.target_urls = self.create_url_list(start_day, end_day)
        self.raw_json_data = []
        try:
            self.scrape_urls()
        except Exception as e:
            print(f"Scraper {self.cinema_id} failed: {e}")

    def create_url_list(self, start_day: int, end_day: int):
        """Return a list of all urls to be scraped for this cinema, i.e. one url for each day in the range of days to be scraped"""
        return [
            f"{base_prefix}{self.cinema_id}/d-{i}/" for i in range(start_day, end_day)
        ]

    def return_data(self):
        """Return all the scraped raw data"""
        return self.raw_json_data

    def scrape_urls(self) -> list:
        """Run scraper on all target urls and process responses"""
        for target_url in self.target_urls:
            base_url = "https://api.scrapingant.com/v2/general"
            params = {
                "url": target_url,
                "x-api-key": scraping_ant_api_key,
                "proxy_country": "FR",
                "browser": "false",
            }

            try:
                response = requests.post(base_url, params=params, json=payload)
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
    def __init__(self, start_day, end_day, save_raw_json_data=False):
        self.all_scraped_json_data = []
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
        for cinema in tqdm(cinema_man.cinema_ids, unit="Cinema"):
            scraper = Scraper(cinema, start_day, end_day)
            data = scraper.return_data()
            for showing in data:
                # Process movie
                movie_man.process_movie(showing)
                # Process showing
                show_man.process_showing(showing, cinema)

    def save_raw_data(self):
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"raw_data_{formatted_time}.json"

        with open(file_name, "w", encoding="utf8") as f:
            json.dump(self.all_scraped_json_data, f, ensure_ascii=False)


if __name__ == "__main__":
    t0 = time.perf_counter()
    scraper_man = ScraperManager(7, 14)

    print(f"Time taken: {time.perf_counter() - t0:.2f}s")
