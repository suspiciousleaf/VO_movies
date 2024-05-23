from base64 import b64decode
from typing import List
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from logging import Logger


class Base64FormatError(ValueError):
    """Custom error that is raised when an invalid Base64 string is checked"""

    def __init__(self, value: str, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class ListStringError(ValueError):
    """Custom error that is raised when the value checked isn't a list of strings"""

    def __init__(self, value: List[str], message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class IntError(ValueError):
    """Custom error that is raised when the value is not a valid number in the permissable range"""

    def __init__(self, value: int, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


class RatingError(ValueError):
    """Custom error that is raised when the value is not a valid rating (float 0-10)"""

    def __init__(self, value: float, message: str):
        self.value = value
        self.message = message
        super().__init__(message)


# arbitrary_types_allowed=True is to allow the Logger type object through, which Pydantic doesn't know how to fully validate
class MovieModel(BaseModel, arbitrary_types_allowed=True):
    """Model to ensure the movie data is in the correct format before inserting into the database"""

    logger: Logger
    movie_id: str = Field(..., min_length=12, max_length=191)
    original_title: str = Field(..., min_length=2, max_length=191)
    french_title: str = Field(..., min_length=2, max_length=191)
    cast: str | None = None
    languages: str | None = None
    genres: str | None = None
    release_date: datetime | None = None

    @field_validator("movie_id")
    def movie_id_is_valid_base64(cls, movie_id):
        try:
            b64decode(movie_id, validate=True)
            return movie_id
        except:
            raise Base64FormatError(value=movie_id, message="Invalid Base64 string")

    @field_validator("cast", "languages", "genres", mode="before")
    def validate_list(cls, input_list, values):
        try:
            if input_list is None:
                return None

            # Check all items in the list are strings
            if not all(isinstance(item, str) for item in input_list):
                list_types = [type(item) for item in input_list if type(item) != str]
                raise ListStringError(
                    value=input_list,
                    message=f"All items must be strings: input contains {list_types}",
                )

            # Check if the combined length of all items, plus separators, is less than or equal to 191 characters to comply with database VARCHAR(191)
            input_as_csv_length = len(",".join(input_list))
            if input_as_csv_length > 191:
                raise ListStringError(
                    value=input_list,
                    message=f"Length of input as csv must be < 191: actual = {input_as_csv_length}",
                )

            return ",".join(input_list)
        except Exception as e:
            logger = values.data.get("logger")
            if logger:
                logger.warning(
                    f"Movie.{values.field_name} csv list validation failed. {e}"
                )
            return None


class AdditionalDataMovieModel(BaseModel, arbitrary_types_allowed=True):
    """Model to ensure the additional movie data from TMDB is in the correct format before inserting into the database"""

    logger: Logger
    origin_country: str | None = Field(None, max_length=191)
    rating: float | None = None
    tagline: str | None = Field(None, max_length=255)
    runtime: int | None = None
    synopsis: str | None = Field(None, max_length=1000)
    imdb_url: str | None = Field(None, max_length=255)
    poster_lo_res: str | None = Field(None, max_length=255)
    poster_hi_res: str | None = Field(None, max_length=255)
    tmdb_id: int | None = None

    @field_validator("runtime", mode="before")
    def validate_smallint_un(cls, input, values):
        try:
            if input is None:
                return None
            if not isinstance(input, int):
                raise IntError(
                    value=input,
                    message=f"Movie.runtime must be an int, not {type(input)}",
                )
            if not 0 < input <= 65535:
                raise IntError(
                    value=input,
                    message=f"Movie.runtime={input} outside permissable range (0-65535)",
                )
            return input

        except Exception as e:
            logger = values.data.get("logger")
            if logger:
                logger.warning(e)
            return None

    @field_validator("tmdb_id", mode="before")
    def validate_int_un(cls, input, values):
        try:
            if input is None:
                return None
            if not isinstance(input, int):
                raise IntError(
                    value=input,
                    message=f"Movie.tmdb_id must be an int, not {type(input)}",
                )
            if not 0 < input <= 4294967295:
                raise IntError(
                    value=input,
                    message="Movie.tmdb_id={input} outside permissable range (0-4294967295)",
                )
            return input

        except Exception as e:
            logger = values.data.get("logger")
            if logger:
                logger.warning(e)
            return None

    @field_validator("rating", mode="before")
    def validate_rating(cls, input, values):
        try:
            if input is None:
                return None
            if input == 0:
                return None
            if not isinstance(input, float):
                raise RatingError(
                    value=input, message=f"Movie.rating not a float: {type(input)}"
                )
            if not 0 < input <= 10:
                raise RatingError(
                    value=input,
                    message="Movie.rating={input} outside permissable range (0 < x <= 10)",
                )
            return input

        except Exception as e:
            logger = values.data.get("logger")
            if logger:
                logger.warning(e)
            return None
