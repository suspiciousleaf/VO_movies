# Need to make one table for each movie with these details, one table with show times that links to the movie table.


class Movie:
    def __init__(
        self,
        original_title: str = "",
        french_title: str = "",
        image_poster: str = "",
        runtime: str = "",
        synopsis: str = "",
        cast: list[str] = [""],
        languages: list[str] = [""],
        genres: list[str] = [""],
        release_year: int = 0,
    ) -> None:
        # Original title
        self.original_title = original_title
        # French title
        self.french_title = french_title
        # Poster image url
        self.image_poster = image_poster
        # Runtime
        self.runtime = runtime
        # Synopsis
        self.synopsis = synopsis
        # Main cast
        self.cast = cast
        # Language(s)
        self.languages = languages
        # Genre(s)
        self.genres = genres
        # Release year
        self.release_year = release_year

    def __str__(self):
        return f"Original Title: {self.original_title} \nFrench Title: {self.french_title} \nPoster: {self.image_poster} \nRumtime: {self.runtime} \nSynopsis:{self.synopsis} \nCast: {self.cast} \nLanguages: {self.languages} \nGenre(s): {self.genres} \nRelease Year: {self.release_year}"

    def __repr__(self):
        return f"Movie('{self.original_title}', '{self.french_title}', '{self.image_poster}', '{self.runtime}', '{self.synopsis}', {self.cast}, {self.languages}, {self.genres}, {self.release_year})"
