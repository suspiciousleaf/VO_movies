from fastapi import APIRouter, HTTPException, Request

from routers.fastapi_cinema_model import CinemaModel
from cinema import CinemaManager
from routers.limiter import limiter


router = APIRouter(
    prefix="/cinema",
)


@router.get("/", status_code=200)
@limiter.limit("1/second")
def get_cinemas(request: Request):
    try:
        cinema_man = CinemaManager()
        return cinema_man.retrieve_cinema_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")


@router.post("/add", status_code=201)
@limiter.limit("1/second")
async def add_cinema(request: Request, cinema: CinemaModel):
    cinema_man = CinemaManager()
    response = await cinema_man.add_cinema_to_database(cinema.__dict__)
    response["payload"] = cinema
    if response["ok"]:
        return response
    else:
        raise HTTPException(status_code=response["code"], detail=response["info"])
