from contextlib import asynccontextmanager

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
from creds import SCRAPER_CODE, ORIGINS


def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger = request.app.state.logger
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle management"""
    # Initialize logger and run setup
    logger = getLogger(__name__)
    setup_logging()
    app.state.logger = logger
    app.state.search = Search(logger)  # Store a single instance in app.state
    yield


# Initialize app and search
app = FastAPI(lifespan=lifespan)

# CORS permissions

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
@app.get("/", tags=["Server Health Check"])
@limiter.limit("2/second;20/minute")
def ping(request: Request) -> str:
    return "V.O.Flix is running."


# Endpoint to activate scraper manually
@app.get("/run", tags=["Initiate Scraper"])
@limiter.limit("1/30seconds")
def run_scraper(
    request: Request,
    start: int = 0,
    end: int = 14,
    auth: str | None = Header(None),
):
    """Endpoint that can be used to initialize the scraper"""
    import time

    from scraper import ScraperManager

    logger = request.app.state.logger

    if not auth or auth.strip() != SCRAPER_CODE:
        logger.error(
            f"Unauthorized access attempt: Initialize scraper days {start} - {end}"
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
        )

    t0 = time.perf_counter()

    try:
        ScraperManager(
            start_day=start,
            end_day=end,
            logger=logger,
        )
        logger.info(f"Time taken: {time.perf_counter() - t0:.2f}s")
        return f"Scraper ran successfully, days {start} - {end}"
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail={"message": "Server Error"})
