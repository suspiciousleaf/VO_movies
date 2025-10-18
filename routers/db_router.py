from fastapi import APIRouter, HTTPException, Request, Depends

from build_db import build_db
from db_utilities import test_db_connection
from routers.limiter import limiter
from dependencies import get_logger


router = APIRouter(
    prefix="/db",
)


@router.get("/", status_code=200, tags=["Database"])
@limiter.limit("2/second;20/minute")
def test_database_connection(request: Request, logger=Depends(get_logger)):
    logger.info("Received request to test database connection")
    try:
        result = test_db_connection(logger=logger)
        logger.info(f"Database connection test result: {result}")
        return result
    except Exception as e:
        logger.error(f"Database connection test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database connection test failed, please try again later: {e}",
        )


@router.get("/build", status_code=200, tags=["Database"])
@limiter.limit("2/second;20/minute")
def validate_database_schema(request: Request, logger=Depends(get_logger)):
    try:
        result = build_db(logger=logger)
        return result
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={"message": e})
