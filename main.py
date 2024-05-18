from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from routers.cinema_router import router as cinema_router
from routers.showings_router import router as showings_router
from routers.limiter import limiter
from search import Search
from logging import getLogger
from logs.setup_logger import setup_logging
from routers.cinema_model import GPSInvalidError


# Initialize logger and run setup
logger = getLogger(__name__)
setup_logging()


def validation_exception_handler(request: Request, exc: GPSInvalidError):
    client_ip = request.client.host
    logger.error(f"Validation error from IP {client_ip}:")  # {exc.errors()}")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {"detail": exc.message}
        ),  # ({"detail": exc.errors()}),
    )


# Initialize app and search
app = FastAPI()
search = Search()

# Add logger to app state
app.state.logger = logger

# Add routers
app.include_router(cinema_router)
app.include_router(showings_router)

# Add custom exception handler
app.add_exception_handler(GPSInvalidError, validation_exception_handler)

# Add rate limiter and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Endpoint to ping server
@app.get("/")
@limiter.limit("1/second")
def ping(request: Request) -> str:
    return "The server is running."


# TODO End point to modify cinemas, add info, and end point to delete cinemas á la CRUD. Maybe add additional scraper to get cinema details
