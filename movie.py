# Need to make one table for each movie with these details, one table with show times that links to the movie table.


class Movie:
    def __init__(
        self,
        original_title: str = "",
        french_title: str = "",
        image_poster: str = "",
        runtime_min: int = 0,
        synopsis: str = "",
        cast: list[str] = [],
        genres: list[str] = [],
        release_year: int = 0,
    ) -> None:
        # Original title
        self.original_title = original_title
        # French title
        self.french_title = french_title
        # Poster image url
        self.image_poster = image_poster
        # Runtime
        self.runtime = runtime_min
        # Synopsis
        self.synopsis = synopsis
        # Main cast
        self.cast = cast
        # Genre(s)
        self.genres = genres
        # Release year
        self.release_year = release_year
