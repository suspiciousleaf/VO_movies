import requests
import json
from pprint import pprint
import datetime
from creds import *
from cinema import CinemaManager
from showing import ShowingsManager
from movie import MovieManager

cinema_man = CinemaManager()
show_man = ShowingsManager()
movie_man = MovieManager()

SAVE_RAW_JSON = False

if SAVE_RAW_JSON:
    raw_json = []
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"raw_data_{formatted_time}.json"


class Scraper:
    def __init__(self, cinema_id: str, start_day: int, end_day: int) -> None:
        self.cinema_id = cinema_id
        self.target_urls = self.create_url_list(start_day, end_day)
        try:
            self.scrape_urls()
        except Exception as e:
            print(f"Scraper {self.cinema_id} failed: {e}")

    def create_url_list(self, start_day: int, end_day: int):
        """Return a list of all urls to be scraped for this cinema, i.e. one url for each day in the range of days to be scraped"""
        return [
            f"{base_prefix}{self.cinema_id}/d-{i}/" for i in range(start_day, end_day)
        ]

    def scrape_urls(self) -> list:
        """Run scraper on all target urls and process responses"""
        for target_url in self.target_urls:
            #! Delete below
            print(f"Scraping target: {target_url})")
            base_url = "https://api.scrapingant.com/v2/general"
            payload = {"filters": [{"showtimes.version": ["ORIGINAL"]}]}
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
                                if SAVE_RAW_JSON:
                                    raw_json.append(showing)
                                # Process movie
                                movie_man.process_movie(showing)
                                # Process showing
                                show_man.process_showing(showing, self.cinema_id)

            except Exception as e:
                print(f"Error: {response.status_code=}, Exception: {e}")


class ScraperManager:
    def __init__(self, start_day, end_day):
        self.run_scrapers(start_day, end_day)
        print(movie_man)
        movie_man.add_new_movies_to_database()
        print(show_man)
        show_man.add_new_showings_to_database()

    def run_scrapers(self, start_day, end_day):
        for cinema in cinema_man:
            Scraper(cinema, start_day, end_day)


if SAVE_RAW_JSON:
    with open(file_name, "w", encoding="utf8") as f:
        json.dump(raw_json, f, ensure_ascii=False)
