from fastapi import APIRouter, HTTPException, Request, Depends

from search import Search
from routers.limiter import limiter
from dependencies import get_logger


router = APIRouter(
    prefix="/search",
)


def get_search(request: Request) -> Search:
    """Retrieve the persistent Search instance from app state"""
    return request.app.state.search


@router.get("", status_code=200, tags=["Search"])
@limiter.limit("2/second;20/minute")
def find_showings(
    request: Request,
    logger=Depends(get_logger),
    search=Depends(get_search),
) -> list | dict:
    try:
        data = search.search()
        logger.info(
            f"Search.search() called, returned {len(data.get('showings', []))} results."
        )
        return data

    except Exception as e:
        logger.error(f"Search.search() failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Request failed, please try again later"
        )
