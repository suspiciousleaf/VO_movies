from fastapi import FastAPI, Query, HTTPException

from search import Search
from cinema import CinemaManager
from fastapi_cinema_model import CinemaModel

app = FastAPI()
search = Search()


@app.get("/")
def index() -> str:
    return "hello"


@app.get("/search")
def find_showings(towns: str | None = Query(default=None, min_length=3)) -> list:
    if towns is None:
        return search.search()
    else:
        towns = towns.split(",")
        return search.search(towns)


@app.post("/add_cinema", status_code=201)
def create_cinema(cinema: CinemaModel):
    cinema_man = CinemaManager()
    response = cinema_man.add_cinema_to_database(cinema.__dict__)
    response["payload"] = cinema
    if response["ok"]:
        return response
    else:
        raise HTTPException(status_code=response["code"], detail=response["info"])


# TODO End point to insert new cinema into database, maybe end point to modify cinemas, add info, and end point to delete cinemas á la CRUD. Maybe add additional scraper to get cinema details
