from fastapi import FastAPI, Query

from search import Search

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
