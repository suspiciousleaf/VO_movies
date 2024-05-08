from fastapi import APIRouter, HTTPException, Request

from showing import ShowingsManager
from routers.limiter import limiter


router = APIRouter(
    prefix="/showings",
)
