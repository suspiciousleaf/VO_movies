from contextlib import asynccontextmanager
import time
import asyncio
from logging import getLogger

from fastapi import FastAPI, Request, Response, HTTPException, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from routers.cinema_router import router as cinema_router
from routers.search_router import router as search_router
from routers.db_router import router as db_router
from routers.limiter import limiter
from search import Search
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
    app.state.search = Search(logger)
    yield


# Initialize app
app = FastAPI(lifespan=lifespan)

# Rate limiter middleware
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS permissions
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Retry-After",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

# Include routers
app.include_router(cinema_router)
app.include_router(search_router)
app.include_router(db_router)

# Custom exception handler for validation errors
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# Endpoint to ping server
@app.get("/", tags=["Server Health Check"])
@limiter.limit("2/second;20/minute")
def ping(request: Request, response: Response) -> str:
    return "V.O.Flix API is running."
