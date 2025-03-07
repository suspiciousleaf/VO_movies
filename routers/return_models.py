from typing_extensions import Annotated
from pydantic import (
    BaseModel,
    StringConstraints,
    HttpUrl,
    PrivateAttr,
    RootModel,
    field_validator,
)
from datetime import date


class MovieData(BaseModel):
    _movie_id: str = PrivateAttr()
    runtime: int | None
    synopsis: str | None
    cast: str
    genres: str
    release_date: date | None
    rating_imdb: float | None
    rating_rt: int | None
    rating_meta: int | None
    imdb_url: HttpUrl | str
    poster_hi_res: HttpUrl
    poster_lo_res: HttpUrl

    # If any values are None, return an empty string instead
    @field_validator("imdb_url", "cast", "genres", mode="before")
    def empty_string_instead_of_None(cls, value):
        return value or ""


class MovieCollection(RootModel):
    root: dict[str, MovieData]


class StartTime(BaseModel):
    time: str
    date: str
    year: str

    class Config:
        """This is used by the SwaggerUI automatic documentation to prefil the endpoint testing"""

        json_schema_extra = {
            "example": {"time": "19:00", "date": "11 March", "year": "2025"}
        }


class ShowingData(BaseModel):
    cinema: Annotated[str, StringConstraints(min_length=5, pattern=r"^.+,.+$")]
    original_title: str
    start_time: StartTime

    class Config:
        """This is used by the SwaggerUI automatic documentation to prefil the endpoint testing"""

        json_schema_extra = {
            "example": {
                "cinema": "Castillet,Perpignan",
                "original_title": "WALL-E",
                "start_time": {"time": "19:00", "date": "11 March", "year": "2030"},
            }
        }
