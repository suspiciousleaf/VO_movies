from typing_extensions import Annotated
from pydantic import BaseModel, StringConstraints
from datetime import datetime


class ShowingModel(BaseModel):
    """Model to ensure the showing data is in the correct format before inserting into the database"""

    movie_id: Annotated[str, StringConstraints(min_length=12, max_length=191)]
    cinema_id: Annotated[
        str, StringConstraints(min_length=5, max_length=5, pattern=r"^[A-Z]\d{4}$")
    ]
    start_time: datetime
