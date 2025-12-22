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
REFERER = getenv("REFERER")
PAYLOAD = json.loads(getenv("PAYLOAD"))
CINEMA_CODE = getenv("CINEMA_CODE")
DATA_REFRESH_AGE = int(getenv("DATA_REFRESH_AGE"))
OMDB_API_URL = getenv("OMDB_API_URL")
OMDB_API_KEY = getenv("OMDB_API_KEY")


def get_origin_list(env_var: str) -> list[str]:
    return getenv(env_var, "").split(",") if getenv(env_var) else []


PROD_URLS = get_origin_list("PROD_URLS")
TEST_URLS = get_origin_list("TEST_URLS")

ORIGINS = PROD_URLS + TEST_URLS if PROD_URLS else ["*"]
