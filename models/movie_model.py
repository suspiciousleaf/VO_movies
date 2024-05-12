from base64 import b64decode
from typing_extensions import Annotated
from typing import List
from pydantic import BaseModel, StringConstraints, validator
from datetime import datetime


class MovieModel(BaseModel):
    """Model to ensure the movie data is in the correct format before inserting into the database"""

    movie_id: Annotated[str, StringConstraints(min_length=12, max_length=191)]
    original_title: Annotated[str, StringConstraints(min_length=2, max_length=191)]
    french_title: Annotated[str, StringConstraints(min_length=2, max_length=191)]
    image_poster: Annotated[str, StringConstraints(max_length=255)] | None = None
    runtime: Annotated[str, StringConstraints(max_length=16)] | None = None
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
            raise ValueError("Invalid Base64 string")

    @validator("cast", "languages", "genres")
    def validate_list(cls, input_list):
        if input_list is None:
            return None

        # Check all items in the list are strings
        if not all(isinstance(item, str) for item in input_list):
            raise ValueError("All items in list must be strings")

        # Check if the combined length of all items, plus separators, is less than or equal to 191 characters to comply with database VARCHAR(191)
        if len(",".join(input_list)) > 191:
            raise ValueError("Length of list as csv must be max 191 characters")

        return input_list
