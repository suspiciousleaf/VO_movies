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
        client_ip = request.client.host
        logger.info(f"/get_cinemas endpoint requested from IP: {client_ip}")
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
    cinema_man = CinemaManager(logger)
    client_ip = request.client.host
    logger.info(
        f"/add (cinema) endpoint requested from IP: {client_ip}: {cinema.__dict__}"
    )
    response = await cinema_man.add_cinema_to_database(cinema.__dict__)
    response["payload"] = cinema
    if response["ok"]:
        return response
    else:
        logger.error(f"CinemaManager.add_cinema() failed: {response['info']}")
        raise HTTPException(status_code=response["code"], detail=response["info"])


@router.delete("/delete")
@limiter.limit("1/second")
async def delete_cinema(
    request: Request, cinema_id: CinemaDelete, logger=Depends(get_logger)
):
    cinema_man = CinemaManager(logger)
    client_ip = request.client.host
    logger.info(f"/delete endpoint requested from IP: {client_ip}")
    response = cinema_man.delete_cinema(cinema_id=cinema_id.__dict__)
    response["payload"] = cinema_id
    if response["ok"]:
        return response
    else:
        logger.error(f"CinemaManager.delete_cinema() failed: {response['info']}")
        raise HTTPException(status_code=response["code"], detail=response["info"])
