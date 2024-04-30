from datetime import datetime
from pprint import pprint

from db_utilities import connect_to_database

TABLE_NAME = "movies"

# We have a list of movie_id's from the database. We get a list of (movie, showings) from the scraper. We want to loop through the list. For each movie, we want to see if that movie_id is in the database, and if not, add that new movie to movies table. We also want to view all showings for that item in the list, see which aren't in the showings table, and add them.


class Movie:

    @staticmethod
    def get_columns() -> tuple[str]:
        """Returns a tuple of the database column names to be written to"""
        return (
            "movie_id",
            "original_title",
            "french_title",
            "image_poster",
            "runtime",
            "synopsis",
            "cast",
            "languages",
            "genres",
            "release_date",
        )

    def __init__(
        self,
        # `movie_id` is a 16 character with padding Base64 encoding of f"Movie:{showing['movie']['internalId']}"
        movie_id: str | None = None,
        original_title: str | None = None,
        french_title: str | None = None,
        image_poster: str | None = None,
        runtime: str | None = None,
        synopsis: str | None = None,
        cast: list[str] | None = None,
        languages: list[str] | None = None,
        genres: list[str] | None = None,
        release_date: datetime | None = None,
    ) -> None:
        # ID
        self.movie_id = movie_id
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
        self.cast = ",".join(cast)
        # Language(s)
        self.languages = ",".join(languages)
        # Genre(s)
        self.genres = ",".join(genres)
        # Release date
        self.release_date = release_date

    def __str__(self) -> str:
        return f"Movie ID: {self.movie_id} \nOriginal Title: {self.original_title} \nFrench Title: {self.french_title} \nPoster: {self.image_poster} \nRuntime: {self.runtime} \nSynopsis:{self.synopsis} \nCast: {self.cast} \nLanguages: {self.languages} \nGenre(s): {self.genres} \nRelease Date: {self.release_date}"

    def __repr__(self) -> str:
        return f"Movie('{self.movie_id}', '{self.original_title}', '{self.french_title}', '{self.image_poster}', '{self.runtime}', '{self.synopsis}', {self.cast}, {self.languages}, {self.genres}, {self.release_date})"


class MovieManager:
    def __init__(self) -> None:
        self.current_movie_ids = set(self.retrieve_movies())
        self.new_movies = []

    @connect_to_database
    def retrieve_movies(self, db, cursor) -> list[tuple[str]]:
        try:
            query = f"SELECT movie_id FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            return results

        except Exception as e:
            print(f"MovieManager.retrieve_movies: An error occurred: {str(e)}")

    def movie_already_in_database(self, movie_id) -> bool:
        """Check if movie_id is recognised. Return False if movie needs to be added"""
        return (movie_id,) in self.current_movie_ids

    def add_new_movie(self, new_movie: Movie) -> None:
        """Takes a movie & showing item from scraped json that isn't in the database, creates a new Movie object to add to database, and adds the movie_id to the set of current movie_ids to prevent additional copies being added."""
        self.new_movies.append(new_movie)
        self.current_movie_ids.add((new_movie.movie_id,))

    def process_movie(self, item: dict) -> None:
        movie_id = item["movie"]["id"]
        if not self.movie_already_in_database(movie_id):
            new_movie = self.create_movie(item)
            self.add_new_movie(new_movie)

    def create_movie(self, item: dict) -> Movie:
        """Creates a Movie object from the raw json data

        Args:
            item (dict): raw movie data from request, single movie at a time

        Returns:
            Movie object
        """
        movie_id = item["movie"]["id"]
        original_title = item["movie"]["originalTitle"]
        french_title = item["movie"]["title"]
        synopsis = item["movie"]["synopsis"]
        image_poster = item["movie"]["poster"]["url"]
        runtime = item["movie"]["runtime"]
        genres = [genre["tag"].title() for genre in item["movie"]["genres"]]
        languages = [language.title() for language in item["movie"]["languages"]]

        cast = []
        for cast_raw in item["movie"]["cast"]["edges"]:
            try:
                # Below is to deal with some cast members having only first or last name
                cast_member = cast_raw["node"]["actor"]
                first_name = cast_member["firstName"] or ""
                last_name = cast_member["lastName"] or ""
                name = " ".join([first_name, last_name]).strip()

                cast.append(name)

            except:
                continue

        # Find release date - if note available, use production date instead
        release_date = None
        for release in item["movie"]["releases"]:
            if release["__typename"] == "MovieRelease" and release["releaseDate"]:
                try:
                    date_str = release["releaseDate"]["date"]
                    release_date = datetime.strptime(date_str, "%Y-%m-%d")
                    break
                except:
                    continue
        if not release_date:
            try:
                date_str = str(item["movie"]["data"]["productionYear"]) + ("-01-01")
                release_date = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                pass

        return Movie(
            movie_id,
            original_title,
            french_title,
            image_poster,
            runtime,
            synopsis,
            cast,
            languages,
            genres,
            release_date,
        )

    @connect_to_database
    def add_new_movies_to_database(self, db=None, cursor=None) -> None:
        """Run this to add all new movies stored in self.new_movies to database"""

        # List of dicts of values for each new movie to be inserted into {TABLE_NAME} table
        movie_values_list = [movie.__dict__ for movie in self.new_movies]

        # All columns to be inserted into {TABLE_NAME} table
        columns = Movie.get_columns()
        # Create placeholders for values to be inserted
        placeholders = ", ".join(f"%({key})s" for key in columns)
        # Create INSERT query
        insert_query = (
            f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders});"
        )
        # Execute above query to insert new showings into database
        cursor.executemany(insert_query, movie_values_list)
        # Commit changes to database
        db.commit()
