from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from routers.cinema_router import router as cinema_router
from routers.search_router import router as search_router
from routers.db_router import router as db_router
from routers.limiter import limiter
from search import Search
from logging import getLogger
from logs.setup_logger import setup_logging


# Initialize logger and run setup
logger = getLogger(__name__)
setup_logging()


def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


# Initialize app and search
app = FastAPI()
search = Search(logger)

# Add logger to app state
app.state.logger = logger

# Add routers
app.include_router(cinema_router)
app.include_router(search_router)
app.include_router(db_router)

# Add custom exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Add rate limiter and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Endpoint to ping server
@app.get("/")
@limiter.limit("1/second")
def ping(request: Request) -> str:
    return "The server is running."


@app.get("/run")
def run_scraper(start: int = 0, end: int = 14):
    import time

    from scraper import ScraperManager

    t0 = time.perf_counter()

    try:
        scraper_man = ScraperManager(
            start=start,
            end=end,
            logger=logger,
        )
        logger.info(f"Time taken: {time.perf_counter() - t0:.2f}s")
        return f"Scraper ran successfully, days {start} - {end}"
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={"message": "Server Error"})
