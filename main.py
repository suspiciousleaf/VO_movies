from os import getenv

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

if getenv("SCRAPER_CODE") is None:
    from dotenv import load_dotenv

    load_dotenv()

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

# CORS permissions

origins = [
    getenv("PROD_URL"),
    getenv("TEST_URL"),
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create search
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
    return "VOFlix is running."


# Endpoint to activate scraper manually
@app.get("/run")
@limiter.limit("1/30seconds")
def run_scraper(
    request: Request,
    start: int = 0,
    end: int = 14,
    authorization: str = Header(None),
):
    """Endpoint that can be used to initialize the scraper"""
    import time

    from scraper import ScraperManager

    SCRAPER_CODE = getenv("SCRAPER_CODE")

    if authorization != SCRAPER_CODE:
        logger.error(
            f"Unauthorized access attempt: Initialize scraper days {start} - {end}"
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
        )

    t0 = time.perf_counter()

    try:
        scraper_man = ScraperManager(
            start_day=start,
            end_day=end,
            logger=logger,
        )
        logger.info(f"Time taken: {time.perf_counter() - t0:.2f}s")
        return f"Scraper ran successfully, days {start} - {end}"
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={"message": "Server Error"})
