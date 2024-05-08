from fastapi import APIRouter, Query, HTTPException, Request

from search import Search
from routers.limiter import limiter


router = APIRouter(
    prefix="/showings",
)


@router.get("/search", status_code=200)
@limiter.limit("1/second")
def find_showings(
    request: Request, towns: str | None = Query(default=None, min_length=3)
) -> list:
    search = Search()
    if towns is None:
        return search.search()
    else:
        towns = towns.split(",")
        return search.search(towns)
