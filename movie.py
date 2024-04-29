from datetime import datetime
from pprint import pprint

from db_utilities import connect_to_database

# We have a list of movie_id's from the database. We get a list of (movie, showings) from the scraper. We want to loop through the list. For each movie, we want to see if that movie_id is in the database, and if not, add that new movie to movies table. We also want to view all showings for that item in the list, see which aren't in the showings table, and add them.


class Movie:
    #! Add method to return something that can be used to add movie to database
    def __init__(
        self,
        # `movie_id` is a 16 character with padding Base64 encoding of f"Movie:{showing['movie']['internalId']}"
        movie_id: str = "",
        original_title: str = "",
        french_title: str = "",
        image_poster: str = "",
        runtime: str = "",
        synopsis: str = "",
        cast: list[str] = [""],
        languages: list[str] = [""],
        genres: list[str] = [""],
        release_date: int = 0,
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
        self.cast = cast
        # Language(s)
        self.languages = languages
        # Genre(s)
        self.genres = genres
        # Release year
        self.release_date = release_date

    def __str__(self):
        return f"Movie ID: {self.movie_id} \nOriginal Title: {self.original_title} \nFrench Title: {self.french_title} \nPoster: {self.image_poster} \nRuntime: {self.runtime} \nSynopsis:{self.synopsis} \nCast: {self.cast} \nLanguages: {self.languages} \nGenre(s): {self.genres} \nRelease Date: {self.release_date}"

    def __repr__(self):
        return f"Movie('{self.movie_id}', '{self.original_title}', '{self.french_title}', '{self.image_poster}', '{self.runtime}', '{self.synopsis}', {self.cast}, {self.languages}, {self.genres}, {self.release_date})"


class MovieManager:
    def __init__(self):
        self.current_movie_ids = set(
            ["TW92aWU6MjY5MTIy", "TW92aWU6Mjc4NzQy", "TW92aWU6Mjg2NDM3"]
        )  # set(self.retrieve_movies())
        self.new_movies = []

    @connect_to_database
    def retrieve_movies(self, db, cursor):
        try:
            cursor = db.cursor()
            table_name = "movies"
            query = f"SELECT movie_id FROM {table_name};"
            cursor.execute(query)
            results = cursor.fetchall()

            return results

        except Exception as e:
            print(f"MovieManager.retrieve_movies: An error occurred: {str(e)}")

    def verify_movie_id_in_current_movies(self, movie_id):
        """Check if movie_id is recognised. Return False if movie needs to be added"""
        return movie_id in self.current_movie_ids

    def add_new_movie(self, item):
        """Takes a movie & showing item from scraped json that isn't in the database, creates a new Movie object to add to database, and adds the movie_id to the set of current movie_ids to prevent additional copies being added."""
        self.new_movies.append(self.create_movie(item))
        self.current_movie_ids.add(item["movie"]["id"])

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
                cast_member = cast_raw["node"]["actor"]
                first_name = cast_member["firstName"] or ""
                last_name = cast_member["lastName"] or ""
                name = " ".join([first_name, last_name]).strip()

                cast.append(name)

            except:
                continue

        release_date = None
        for release in item["movie"]["releases"]:
            if release["__typename"] == "MovieRelease" and release["releaseDate"]:
                try:
                    date_str = release["releaseDate"]["date"]
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    release_date = date_obj.strftime("%#dth %B %Y")
                    break
                except:
                    continue
        if not release_date:
            date_str = str(item["movie"]["data"]["productionYear"]) + ("-01-01")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            release_date = date_obj.strftime("%#dth %B %Y")

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
