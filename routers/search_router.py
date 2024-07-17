from fastapi import APIRouter, Query, HTTPException, Request, Depends

from search import Search
from routers.limiter import limiter
from dependencies import get_logger


router = APIRouter(
    prefix="/search",
)


@router.get("", status_code=200)
@limiter.limit("2/second;20/minute")
def find_showings(
    request: Request,
    towns: str | None = Query(default=None, min_length=3),
    logger=Depends(get_logger),
) -> list:
    try:
        search = Search(logger)
        if towns is None:
            data = search.search()
        else:
            towns = towns.split(",")
            data = search.search(towns)
        logger.info(f"Search.search() called, returned {len(data)} results. {towns=}")
        return data

    except Exception as e:
        logger.error(f"Search.search() failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Request failed, please try again later"
        )
