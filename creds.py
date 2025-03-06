from os import getenv
import json


if getenv("DB_USER") is None:
    from dotenv import load_dotenv

    load_dotenv()

    DB_PORT = int(getenv("DB_PORT_LOCAL"))
    DB_USER = getenv("DB_USER_LOCAL")
    DB_PASSWORD = getenv("DB_PASSWORD_LOCAL")
    DB_HOST = getenv("DB_HOST_LOCAL")
    DB_NAME = getenv("DB_NAME_LOCAL")

else:
    DB_PORT = int(getenv("DB_PORT"))
    DB_USER = getenv("DB_USER")
    DB_PASSWORD = getenv("DB_PASSWORD")
    DB_HOST = getenv("DB_HOST")
    DB_NAME = getenv("DB_NAME")

SCRAPER_CODE = getenv("SCRAPER_CODE")
TMDB_API_TOKEN = getenv("TMDB_API_TOKEN")
SCRAPING_ANT_API_KEY = getenv("SCRAPING_ANT_API_KEY")
BASE_PREFIX = getenv("BASE_PREFIX")
PAYLOAD = json.loads(getenv("PAYLOAD"))
CINEMA_CODE = getenv("CINEMA_CODE")
ORIGINS = getenv("PROD_URLS").split(",") + getenv("TEST_URLS").split(",")
DATA_REFRESH_AGE = int(getenv("DATA_REFRESH_AGE"))
OMDB_API_URL = getenv("OMDB_API_URL")
OMDB_API_KEY = getenv("OMDB_API_KEY")
