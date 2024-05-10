from datetime import datetime
from pprint import pprint
import requests

from db_utilities import connect_to_database
from creds import movies_db_api_key

TABLE_NAME = "movies"

# We have a list of movie_id's from the database. We get a list of (movie, showings) from the scraper. We want to loop through the list. For each movie, we want to see if that movie_id is in the database, and if not, add that new movie to movies table. We also want to view all showings for that item in the list, see which aren't in the showings table, and add them.


class Movie:

    @staticmethod
    def get_columns() -> tuple[str]:
        """Returns a tuple of the database column names to be written to"""
        return (
            "imdb_ref",
            "movie_id",
            "original_title",
            "french_title",
            "rating",
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
        cast: list[str] | None = None,
        languages: list[str] | None = None,
        genres: list[str] | None = None,
        release_date: datetime | None = None,
    ) -> None:
        """Initialize a Movie object with provided attributes."""
        # Movie ID in database
        self.movie_id = movie_id
        # Original title
        self.original_title = original_title
        # French title
        self.french_title = french_title
        # Poster image url
        self.image_poster = image_poster
        # Runtime
        self.runtime = runtime
        # Main cast
        self.cast = ",".join(cast)
        # Language(s)
        self.languages = ",".join(languages)
        # Genre(s)
        self.genres = ",".join(genres)
        # Release date
        self.release_date = release_date

        # Some movie details are not available from the main source, so they are retrived from an API
        extra_movie_data = self.get_additional_details()
        # IMDB Ref
        self.imdb_ref = extra_movie_data.get("imdb_ref")
        # Rating
        self.rating = extra_movie_data.get("rating")
        # Synopsis
        self.synopsis = extra_movie_data.get("synopsis")

    def get_additional_details(self):
        """Retrieve additional details for the movie from an external API.

        Returns:
            dict: A dictionary containing additional details for the movie:
                - imdb_ref (str): The IMDB reference of the movie.
                - rating (float): The rating of the movie.
                - synopsis (str): The synopsis of the movie.
        """

        # Create empty dict to hold additional details
        extra_movie_data = {}

        try:
            ref_url = f"https://moviesdatabase.p.rapidapi.com/titles/search/title/{self.original_title}"
            # Query movies between release date and one year before to allow for possible inconsistent data
            params = {
                "exact": "false",
                "endYear": f"{self.release_date.year}",
                "startYear": f"{self.release_date.year-1}",
                "titleType": "movie",
            }

            headers = {
                "X-RapidAPI-Key": movies_db_api_key,
                "X-RapidAPI-Host": "moviesdatabase.p.rapidapi.com",
            }

            s = requests.Session()
            # IMDB ref must be identified first, then other details can be retrieved
            response = s.get(ref_url, headers=headers, params=params)
            response.raise_for_status()
            if response.json()["results"]:
                extra_movie_data["imdb_ref"] = response.json()["results"][0]["id"]
            # If no results found using title and year, try again without the year.
            else:
                params = {
                    "exact": "false",
                    "titleType": "movie",
                }
                response = s.get(ref_url, headers=headers, params=params)
                response.raise_for_status()
                if response.json()["results"]:
                    extra_movie_data["imdb_ref"] = response.json()["results"][0]["id"]
                else:
                    raise Exception("Movie not found")

            # Dict to store each of the required details, and the keys required to access that data in the json
            required_details = {
                "rating": ("results", "ratingsSummary", "aggregateRating"),
                "plot": ("results", "plot", "plotText", "plainText"),
            }

            for detail, keys in required_details.items():
                try:

                    query_url = f"https://moviesdatabase.p.rapidapi.com/titles/{extra_movie_data['imdb_ref']}?info={detail}"

                    response = s.get(query_url, headers=headers)

                    response.raise_for_status()
                    nested_data = response.json()
                    for key in keys:
                        nested_data = nested_data.get(key, {})

                    if detail == "plot":
                        detail = "synopsis"
                    extra_movie_data[detail] = nested_data
                except:
                    extra_movie_data[detail] = None
        except:
            print(f"{self.original_title}: additional movie details not found")
        return extra_movie_data

    def __str__(self) -> str:
        """Return a string representation of the Movie object."""
        return f"IMDB Ref: {self.imdb_ref} \nMovie ID: {self.movie_id} \nOriginal Title: {self.original_title} \nFrench Title: {self.french_title} \nRating: {self.rating}\nPoster: {self.image_poster} \nRuntime: {self.runtime} \nSynopsis:{self.synopsis} \nCast: {self.cast} \nLanguages: {self.languages} \nGenre(s): {self.genres} \nRelease Date: {self.release_date}"

    def __repr__(self) -> str:
        """Return a string representation of the Movie object for debugging."""
        return f"Movie('{self.imdb_ref}', '{self.movie_id}', '{self.original_title}', '{self.french_title}', '{self.rating}', '{self.image_poster}', '{self.runtime}', '{self.synopsis}', {self.cast}, {self.languages}, {self.genres}, {self.release_date})"

    def movie_name(self):
        """Return the original title of the movie."""
        return f"Name: {self.original_title}"


class MovieManager:
    def __init__(self) -> None:
        """Initialize a MovieManager object."""
        self.current_movie_ids = set(self.retrieve_movies())
        self.new_movies = []

    @staticmethod
    @connect_to_database
    def retrieve_movies(db, cursor) -> list[tuple[str]]:
        """Retrieve existing movie IDs from the database."""
        try:
            query = f"SELECT movie_id FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            # Convert list of tuples to list of strings
            return [result[0] for result in results]

        except Exception as e:
            print(f"MovieManager.retrieve_movies: An error occurred: {str(e)}")

    def movie_already_in_database(self, movie_id: str) -> bool:
        """Check if a movie is already in the database."""
        return movie_id in self.current_movie_ids

    def add_new_movie(self, new_movie: Movie) -> None:
        """Takes a movie & showing item from scraped json that isn't in the database, creates a new Movie object to add to database, and adds the movie_id to the set of current movie_ids to prevent additional copies being added."""
        self.new_movies.append(new_movie)
        self.current_movie_ids.add(new_movie.movie_id)

    def process_movie(self, item: dict) -> None:
        """Process a movie item from scraped JSON data."""
        movie_id = item["movie"]["id"]
        if not self.movie_already_in_database(movie_id):
            new_movie = self.create_movie(item)
            self.add_new_movie(new_movie)

    def create_movie(self, item: dict) -> Movie:
        """Create a Movie object from raw JSON data."""
        movie_id = item["movie"]["id"]
        original_title = item["movie"]["originalTitle"]
        french_title = item["movie"]["title"]
        # synopsis = item["movie"]["synopsis"]
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
            # synopsis,
            cast,
            languages,
            genres,
            release_date,
        )

    @connect_to_database
    def add_new_movies_to_database(self, db=None, cursor=None) -> None:
        """Add new movies to the database."""
        if self.new_movies:

            movie_values_list = [movie.__dict__ for movie in self.new_movies]

            columns = Movie.get_columns()
            placeholders = ", ".join(f"%({key})s" for key in columns)
            insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders});"
            cursor.executemany(insert_query, movie_values_list)
            db.commit()

    def __str__(self):
        """Return a string representation of the MovieManager object."""
        if self.new_movies:
            return f"{len(self.new_movies)} new movie(s) found:\n" + "\n".join(
                [movie.movie_name() for movie in self.new_movies]
            )
        else:
            return "No new movies found."


# An error occurred: 1406 (22001): Data too long for column 'movie_id' at row 18
# An error occurred: 1452 (23000): Cannot add or update a child row: a foreign key constraint fails (`vo_movies`.`showtimes`, CONSTRAINT `fk_movie_id` FOREIGN KEY (`movie_id`) REFERENCES `movies` (`movie_id`))

#! Run again and save data, see what the error is
