from typing_extensions import Annotated
from pydantic import BaseModel, StringConstraints, field_validator


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

    @field_validator("gps")
    def check_gps(cls, gps):
        if gps is None:
            return None
        if len(gps) != 2:
            raise GPSInvalidError(
                gps, f"GPS coordinates must have two elements, not {len(gps)}"
            )
        if not all(isinstance(coord, float) for coord in gps):
            raise GPSInvalidError(gps, "GPS coordinates must be floats")
        if not abs(gps[0]) <= 90 or not abs(gps[1]) <= 180:
            raise GPSInvalidError(gps, "GPS coordinates outside valid range")
        return gps


class CinemaDelete(BaseModel):
    """Validation model for cinema deletion by cinema_id"""

    cinema_id: Annotated[
        str, StringConstraints(min_length=5, max_length=5, pattern=r"^[A-Z]\d{4}$")
    ]


class GPSInvalidError(ValueError):
    """Custom error that is raised when GPS coordinates provided are not valid"""

    def __init__(self, value: str, message: str):
        self.value = value
        self.message = message
        super().__init__(message)
