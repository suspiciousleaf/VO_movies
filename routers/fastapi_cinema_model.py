from typing_extensions import Annotated
from pydantic import BaseModel, StringConstraints, validator


class CinemaModel(BaseModel):
    # Validate input data format. Use Regex to ensure cinema ID is in the correct format. Name and town are required, address, info, and gps are optional
    cinema_id: Annotated[
        str, StringConstraints(min_length=5, max_length=5, pattern=r"^[A-Z]\d{4}$")
    ]
    name: Annotated[str, StringConstraints(min_length=2, max_length=191)]
    address: Annotated[str, StringConstraints(max_length=255)] | None = None
    info: Annotated[str, StringConstraints(max_length=255)] | None = None
    gps: list[float] | None = None
    town: Annotated[str, StringConstraints(min_length=3, max_length=191)]

    @validator("gps")
    def check_gps(cls, gps):
        if gps is None:
            return gps
        if len(gps) != 2:
            raise ValueError("gps coordinates must have exactly two elements")
        if not all(isinstance(coord, float) for coord in gps):
            raise ValueError("gps coordinates must be floats")
        if not all(abs(num) <= 180 for num in gps):
            raise ValueError("gps coordinates outside valid range")
        return gps
