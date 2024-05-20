from fastapi import APIRouter, HTTPException, Request, Depends

from routers.cinema_model import CinemaModel, CinemaDelete
from cinema import CinemaManager
from routers.limiter import limiter
from dependencies import get_logger


router = APIRouter(
    prefix="/cinema",
)


@router.get("/", status_code=200)
@limiter.limit("1/second")
def get_cinemas(request: Request, logger=Depends(get_logger)):
    try:
        logger.info(f"/get_cinemas endpoint requested")
        cinema_man = CinemaManager(logger)
        return cinema_man.retrieve_cinema_info()
    except Exception as e:
        logger.error(f"CinemaManager.get_cinemas() failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Request failed, please try again later"
        )


@router.post("/add", status_code=201)
@limiter.limit("1/second")
async def add_cinema(request: Request, cinema: CinemaModel, logger=Depends(get_logger)):
    try:
        logger.info(f"/add (cinema) endpoint requested: {cinema.__dict__}")
        cinema_man = CinemaManager(logger)
        response = await cinema_man.add_cinema_to_database(cinema.__dict__)
        response["payload"] = cinema.__dict__
        if response["ok"]:
            return response
        else:
            logger.error(f"CinemaManager.add_cinema() failed: {response['info']}")
            raise HTTPException(status_code=response["code"], detail=response["info"])
    except Exception as e:
        logger.error(f"cinema/add endpoint failed: {e}")
        raise HTTPException(status_code=500, detail={"message": "Server Error"})


@router.delete("/delete")
@limiter.limit("1/second")
async def delete_cinema(
    request: Request, cinema_id: CinemaDelete, logger=Depends(get_logger)
):
    try:
        logger.info(f"/delete endpoint requested")
        cinema_man = CinemaManager(logger)
        response = cinema_man.delete_cinema(cinema_id=cinema_id.__dict__, logger=logger)
        response["payload"] = cinema_id
        if response["ok"]:
            return response
        else:
            logger.error(f"CinemaManager.delete_cinema() failed: {response['info']}")
            raise HTTPException(status_code=response["code"], detail=response["info"])
    except:
        logger.error(f"CinemaManager.delete_cinema() failed: {response['info']}")
        raise HTTPException(status_code=500, detail={"message": "Server Error"})
