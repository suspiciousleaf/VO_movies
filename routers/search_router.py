from fastapi import APIRouter, HTTPException, Request, Depends

from search import Search
from routers.return_models import MovieCollection, ShowingData
from routers.limiter import limiter
from dependencies import get_logger


router = APIRouter(
    prefix="/search",
)


def get_search(request: Request) -> Search:
    """Retrieve the persistent Search instance from app state"""
    return request.app.state.search


@router.get("/showings", status_code=200, tags=["Search"])
@limiter.limit("2/second;20/minute")
def find_showings(
    request: Request,
    logger=Depends(get_logger),
    search=Depends(get_search),
) -> list[ShowingData]:
    try:
        data = search.get_showings()
        logger.info(
            f"Search.get_showings() called, returned {len(data or [])} results."
        )
        return data

    except Exception as e:
        logger.error(f"Search.get_showings() failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Request failed, please try again later"
        )


@router.get("/movies", status_code=200, tags=["Search"])
@limiter.limit("2/second;20/minute")
def find_movies(
    request: Request,
    logger=Depends(get_logger),
    search=Depends(get_search),
) -> MovieCollection:
    try:
        data = search.get_movies()
        logger.info(f"Search.get_movies() called, returned {len(data or [])} results.")
        return data

    except Exception as e:
        logger.error(f"Search.get_movies() failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Request failed, please try again later"
        )
