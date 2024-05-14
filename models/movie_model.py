from base64 import b64decode
from typing_extensions import Annotated
from typing import List
from pydantic import BaseModel, StringConstraints, validator
from datetime import datetime


class Base64FormatError(Exception):
    """Custom error that is raised when an invalid Base64 string is checked"""

    def __init__(self, value: str, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class ListStringError(Exception):
    """Custom error that is raised when the value checked isn't a list of strings"""

    def __init__(self, value: List[str], message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class IntError(Exception):
    """Custom error that is raised when the value is not a valid number in the permissable range"""

    def __init__(self, value: int, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class RatingError(Exception):
    """Custom error that is raised when the value is not a valid rating (float 0-10)"""

    def __init__(self, value: float, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class MovieModel(BaseModel):
    """Model to ensure the movie data is in the correct format before inserting into the database"""

    movie_id: Annotated[str, StringConstraints(min_length=12, max_length=191)]
    original_title: Annotated[str, StringConstraints(min_length=2, max_length=191)]
    french_title: Annotated[str, StringConstraints(min_length=2, max_length=191)]
    cast: List[str] | None = None
    languages: List[str] | None = None
    genres: List[str] | None = None
    release_date: datetime | None = None

    @validator("movie_id")
    def movie_id_is_valid_base64(cls, movie_id):
        try:
            b64decode(movie_id, validate=True)
            return movie_id
        except:
            raise Base64FormatError(value=movie_id, message="Invalid Base64 string")

    @validator("cast", "languages", "genres")
    def validate_list(cls, input_list):
        if input_list is None:
            return None

        # Check all items in the list are strings
        if not all(isinstance(item, str) for item in input_list):
            raise ListStringError(
                value=input_list,
                message="One or more items in the list are not strings",
            )

        # Check if the combined length of all items, plus separators, is less than or equal to 191 characters to comply with database VARCHAR(191)
        if len(",".join(input_list)) > 191:
            raise ListStringError(
                value=input_list,
                message="Length of list as csv must be max 191 characters",
            )

        return ",".join(input_list)


class AdditionalDataMovieModel(BaseModel):
    """Model to ensure the additional movie data from TMDB is in the correct format before inserting into the database"""

    origin_country: Annotated[str, StringConstraints(max_length=191)] | None = None
    rating: float | None = None
    tagline: Annotated[str, StringConstraints(max_length=255)] | None = None
    runtime: int | None = None
    synopsis: Annotated[str, StringConstraints(max_length=1000)] | None = None
    imdb_url: Annotated[str, StringConstraints(max_length=255)] | None = None
    poster_lo_res: Annotated[str, StringConstraints(max_length=255)] | None = None
    poster_hi_res: Annotated[str, StringConstraints(max_length=255)] | None = None
    homepage: Annotated[str, StringConstraints(max_length=255)] | None = None
    tmdb_id: int | None = None

    @validator("runtime")
    def validate_smallint_un(cls, input):
        if input is None:
            return None
        if not isinstance(input, int):
            raise IntError(value=input, message="Value is not an integer")
        if not 0 < input <= 65535:
            raise IntError(
                value=input, message="Value outside permissable range (0-65535)"
            )
        return input

    @validator("tmdb_id")
    def validate_int_un(cls, input):
        if input is None:
            return None
        if not isinstance(input, int):
            raise IntError(value=input, message="Value is not an integer")
        if not 0 < input <= 4294967295:
            raise IntError(
                value=input, message="Value outside permissable range (0-4294967295)"
            )
        return input

    @validator("rating")
    def validate_rating(cls, input):
        if input is None:
            return None
        if input == 0:
            return None
        if not isinstance(input, float):
            raise RatingError(value=input, message="Rating not a float")
        if not 0 < input <= 10:
            raise RatingError(value=input, message="Rating not between 0.1 and 10")
        return input
