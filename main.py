from fastapi import FastAPI, Request, HTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from routers.cinema_router import router as cinema_router
from routers.showings_router import router as showings_router
from routers.limiter import limiter
from search import Search


app = FastAPI()
search = Search()

app.include_router(cinema_router)
app.include_router(showings_router)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
@limiter.limit("1/second")
def ping(request: Request) -> str:
    return "The server is running."


# TODO End point to modify cinemas, add info, and end point to delete cinemas á la CRUD. Maybe add additional scraper to get cinema details
