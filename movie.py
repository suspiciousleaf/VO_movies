import unicodedata
from datetime import datetime
from requests import Session, HTTPError
from pydantic import ValidationError
from logging import Logger

from rapidfuzz.distance import JaroWinkler

from models.movie_model import MovieModel, AdditionalDataMovieModel
from db_utilities import connect_to_database
from data.country_info import country_codes
from creds import TMDB_API_TOKEN


TABLE_NAME = "movies"
MAX_RESULTS_BEFORE_YEAR_FILTER = 20

# We have a list of movie_id's from the database. We get a list of (movie, showings) from the scraper. We want to loop through the list. For each movie, we want to see if that movie_id is in the database, and if not, add that new movie to movies table. We also want to view all showings for that item in the list, see which aren't in the showings table, and add them.


# Class to create a movie and gather additional details
class Movie:
    """Represents a movie object with its details. Validates input data using pydantic MovieModel(BaseModel) to ensure it is compatible with database schema.

    Attributes:
        logger (Logger): Logger instance
        movie_id (str): The unique identifier of the movie. Base64 format
        original_title (str): The original title of the movie.
        french_title (str): The French title of the movie.
        cast (list[str], optional): The list of cast members.
        languages (list[str], optional): The list of languages the movie is available in.
        genres (list[str], optional): The list of genres the movie belongs to.
        release_date (datetime, optional): The release date of the movie.

    Methods:
        get_additional_details(): Retrieve additional details for the movie from an external API.
        movie_name(): Return the original title of the movie.
    """

    def __init__(
        self,
        logger: Logger,
        movie_id: str,
        original_title: str,
        french_title: str,
        cast: list[str] | None = None,
        languages: list[str] | None = None,
        genres: list[str] | None = None,
        release_date: datetime | None = None,
    ) -> None:
        self.logger = logger
        data = {
            "movie_id": movie_id,
            "original_title": original_title,
            "french_title": french_title,
            "cast": cast,
            "languages": languages,
            "genres": genres,
            "release_date": release_date,
        }
        try:
            # Validate the input data using MovieModel
            movie_model = MovieModel(**data, logger=logger)

        except ValidationError as e:
            self.logger.error(
                f"MovieModel Validation error for MovieModel with input data: {data}"
            )
            self.logger.error(f"MovieModel Validation error: {e}")
            raise e
        except Exception as e:
            self.logger.error(
                f"Unable to create Movie instance: {e} \n Movie data: {data}"
            )
            raise e

        # If validation succeeds, assign the validated data to attributes
        self.movie_id = movie_model.movie_id
        self.original_title = movie_model.original_title
        self.french_title = movie_model.french_title
        self.cast = movie_model.cast
        self.languages = movie_model.languages
        self.genres = movie_model.genres
        self.release_date = movie_model.release_date

        if isinstance(self.genres, str):
            self.genres = self.genres.replace("_", " ")

        # The info below is not available from the initial source, so it is aquired from TBDM on instantiation. Dict below holds the attribute name for the Movie object, and the key value that stores the information in the json from the API.
        additional_required_details = {
            "original_title": "original_title",
            "origin_country": "origin_country",
            "rating": "vote_average",
            "runtime": "runtime",
            "tagline": "tagline",
            "synopsis": "overview",
            "imdb_url": "imdb_id",
            "poster_slug": "poster_path",
            "tmdb_id": "id",
        }
        extra_movie_data = {}
        try:
            extra_movie_data = self.get_additional_details(additional_required_details)

            if not extra_movie_data.get("original_title"):
                extra_movie_data["original_title"] = self.original_title

            additional_details_movie_model = AdditionalDataMovieModel(
                **extra_movie_data, logger=logger
            )

        except ValidationError as e:
            self.logger.error(
                f"AdditionalDataMovieModel Validation error for input data: {extra_movie_data}"
            )
            self.logger.error(f"AdditionalDataMovieModel Validation error: {e}")
            raise e
        except Exception as e:
            self.logger.error(
                f"Unable to create Movie instance: {e} \n AdditionalDataMovieModel data: {extra_movie_data}"
            )
            raise e

        # Origin countries are given as a csv of ISO 3166-1 alpha-2 codes. This will convert that into a csv of full country names
        if additional_details_movie_model.origin_country is not None:
            try:
                country_list = additional_details_movie_model.origin_country.split(",")
                self.origin_country = ",".join(
                    [country_codes.get(country, "") for country in country_list]
                )
            except:
                self.origin_country = None

        self.original_title = additional_details_movie_model.original_title
        self.rating = additional_details_movie_model.rating
        self.tagline = additional_details_movie_model.tagline
        self.synopsis = additional_details_movie_model.synopsis
        self.imdb_url = additional_details_movie_model.imdb_url
        self.poster_hi_res = additional_details_movie_model.poster_hi_res
        self.poster_lo_res = additional_details_movie_model.poster_lo_res
        self.tmdb_id = additional_details_movie_model.tmdb_id
        self.runtime = additional_details_movie_model.runtime
        self.original_language = additional_details_movie_model.original_language
        self.spoken_languages = additional_details_movie_model.spoken_languages

    def get_additional_details(self, additional_required_details: dict) -> dict:
        """Retrieve additional details for the movie from an TMDB API.

        Returns:
            dict: A dictionary containing additional details for the movie:
                - original_title (str): Original title from TMDB, sometimes not translated in original source.
                - origin_country (str): The country of origin for the movie.
                - rating (float): The average rating of the movie.
                - runtime (int): The runtime of the movie in minutes.
                - tagline (str): The tagline of the movie.
                - synopsis (str): The synopsis of the movie.
                - imdb_url (str): The IMDB URL of the movie.
                - tmdb_id (int): The ID for the movie on TMDB
                - poster_hi_res (str): The URL to the high-resolution poster image of the movie.
                - poster_lo_res (str): The URL to the low-resolution poster image of the movie.
                - rating_imdb
                - rating_rt
                - rating_meta
                - spoken_languages
                - original_language

        Raises:
            Exception: If additional movie details are not found.
        """

        # Create empty dict to hold additional details
        extra_movie_data = {}

        s = Session()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_TOKEN}",
        }

        try:
            id_url = "https://api.themoviedb.org/3/search/movie"

            # TMDB ID must be identified first, then other details can be retrieved. To ensure a correct match when multiple movies have the same title, we retrieve all matches, get extended details for all of them, and then try to match cast members and production year
            queryparams = {
                "query": self.original_title,
            }

            response = s.get(id_url, params=queryparams, headers=headers)
            response.raise_for_status()
            results = response.json().get("results")
            if not results:
                raise Exception("Movie not found on TMDB")

            # If we get too many results due to a generic movie name, or we don't have any cast members to use for matching, run the search again using the production year data that we have. This can be incorrect to is only used if necessary.
            no_cast = not self.cast
            too_many_results = len(results) >= MAX_RESULTS_BEFORE_YEAR_FILTER

            if (no_cast or too_many_results) and self.release_date:
                # Retry with year to narrow results
                queryparams["year"] = str(self.release_date.year)
                response = s.get(id_url, params=queryparams, headers=headers)
                response.raise_for_status()
                results = response.json().get("results", [])
                if not results:
                    raise Exception("Movie not found on TMDB with year filter")

            if results:
                possible_ids: list = [result["id"] for result in results]
            else:
                raise Exception("Movie not found on TMDB")

            params = {"append_to_response": "credits"}
            possible_matches: list = []
            for tmdb_id in possible_ids:
                # Get details for all possible matches
                detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"

                # TMDB ID must be identified first, then other details can be retrieved
                try:
                    response = s.get(detail_url, headers=headers, params=params)
                    response.raise_for_status()
                except HTTPError as e:
                    self.logger.warning(
                        f"HTTP error, Unable to retrieve additional details for TMDB ID {tmdb_id}:{e}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Exception retrieving additional movie details for TMDB ID {tmdb_id}:{e}"
                    )

                response_data = response.json()

                possible_matches.append(self.process_possible_match(response_data))

            best_match = self.find_correct_match(possible_matches)
            if best_match is None:
                raise Exception(
                    f"No confident TMDB match found for '{self.original_title}'"
                )

            # Best match is found, retrieve full details
            chosen_id = best_match["id"]
            detail_url = f"https://api.themoviedb.org/3/movie/{chosen_id}"
            response = s.get(detail_url, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()

            for detail, key in additional_required_details.items():
                info = response_data.get(key)
                extra_movie_data[detail] = (
                    ",".join(info) if isinstance(info, list) else info
                )

            try:
                # TODO Scan through spoken languages or original language, and remove non English
                # Log additional data for monitoring, to remove non English movies scraped in error
                original_language = response_data.get("original_language")
                # iso_639_1 = "en", "fr" etc
                spoken_languages = [
                    language.get("iso_639_1")
                    for language in response_data.get("spoken_languages", [])
                ]
                extra_movie_data["original_language"] = original_language
                extra_movie_data["spoken_languages"] = (
                    ",".join(spoken_languages) if spoken_languages else None
                )

                self.logger.info(
                    f"Scraper additional details for {self.original_title}: {original_language=}, {spoken_languages=}"
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to log additional info for {self.original_title}: {e}"
                )

            # Overwrite production year data with release data from TMDB
            self.release_date = datetime.strptime(
                response_data.get("release_date"), "%Y-%m-%d"
            )

            poster_slug = extra_movie_data.get("poster_slug")

            extra_movie_data["poster_hi_res"] = (
                f"https://image.tmdb.org/t/p/w780{poster_slug}" if poster_slug else None
            )

            extra_movie_data["poster_lo_res"] = (
                f"https://image.tmdb.org/t/p/w342{poster_slug}" if poster_slug else None
            )

            extra_movie_data.pop("poster_slug")

            imdb_slug = extra_movie_data.get("imdb_url")
            if imdb_slug is not None:
                extra_movie_data["imdb_url"] = f"https://www.imdb.com/title/{imdb_slug}"

        except Exception as e:
            self.logger.warning(
                f"{self.original_title}: additional movie details not found: {e}"
            )
            return {}
        finally:
            s.close()
        return extra_movie_data

    def find_correct_match(self, possible_matches: list[dict]) -> dict | None:
        """
        Given a list of processed possible TMDB matches, return the best one based on
        cast member similarity. Returns None if no match scores above threshold.
        """

        if not possible_matches:
            self.logger.warning(f"No possible matches found for {self.original_title}")
            return

        if not self.cast:
            self.logger.info(
                f"'{self.original_title}': no cast available, selecting top TMDB result"
            )
            return possible_matches[0]

        MATCH_THRESHOLD = 0.5

        scored = [
            (match, self._score_cast_against_match(match)) for match in possible_matches
        ]

        scored.sort(key=lambda x: x[1], reverse=True)

        # TODO remove later if all runs smoothly
        for match, score in scored:
            self.logger.info(f"TMDB ID {match.get('id')}: cast match score {score:.2f}")

        best_match, best_score = scored[0] if scored else (None, 0.0)

        if best_score >= MATCH_THRESHOLD:
            self.logger.info(
                f"'{self.original_title}': matched TMDB ID {best_match.get('id')} "
                f"with cast score {best_score:.2f}"
            )
            return best_match

        self.logger.warning(
            f"'{self.original_title}': no confident cast match found, (best score: {best_score:.2f})"
        )
        return None

    @staticmethod
    def process_possible_match(raw_match: dict) -> dict:
        match: dict = {}
        match["id"] = raw_match.get("id")
        match["cast"] = []
        credits = raw_match.get("credits", {})
        for cast_member in credits.get("cast", []):
            name = cast_member.get("original_name")
            if name is not None:
                match["cast"].append(name)
        return match

    @staticmethod
    def _normalise_cast_name(name: str) -> str:
        """Strip accents, lowercase, remove punctuation for comparison."""
        # Decompose unicode characters (e.g. é -> e + combining accent)
        nfkd = unicodedata.normalize("NFKD", name)
        # Drop combining characters (the accents)
        ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
        return ascii_name.lower().strip()

    @staticmethod
    def _name_tokens(name: str) -> tuple[str, str]:
        """Return (last_name, first_initial) tuple for token-based matching."""
        parts = name.split()
        last = parts[-1] if parts else ""
        first_initial = parts[0][0] if len(parts) > 1 else ""
        return last.lower(), first_initial.lower()

    @staticmethod
    def _score_name_match(source_name: str, candidate_name: str) -> float:
        """
        Score how well two names match. Returns 0.0 to 1.0.
        Tries normalised exact match first, then token match, then Jaro-Winkler.
        """
        norm_source = Movie._normalise_cast_name(source_name)
        norm_candidate = Movie._normalise_cast_name(candidate_name)

        # 1. Exact match after normalisation
        if norm_source == norm_candidate:
            return 1.0

        # 2. Token match: last name + first initial
        src_last, src_initial = Movie._name_tokens(norm_source)
        cand_last, cand_initial = Movie._name_tokens(norm_candidate)
        if src_last == cand_last and src_initial == cand_initial:
            return 0.95

        # 3. Jaro-Winkler fuzzy match on full normalised name
        similarity = JaroWinkler.similarity(norm_source, norm_candidate)
        return similarity if similarity >= 0.8 else 0.0

    def _score_cast_against_match(self, possible_match: dict) -> float:
        """
        Score a possible TMDB match against original scraped cast.
        Returns the average best-match score across all cast members in self.cast.
        """
        if not self.cast:
            return 0.0

        candidate_cast = possible_match.get("cast", [])
        if not candidate_cast:
            return 0.0

        total_score = 0.0
        cast_members = self.cast.split(",")
        for source_name in cast_members:
            # Find the best match for this cast member in the candidate's cast list
            best = max(
                (self._score_name_match(source_name, c) for c in candidate_cast),
                default=0.0,
            )
            total_score += best

        return total_score / len(cast_members)

    @staticmethod
    def get_columns() -> tuple[str, ...]:
        """Returns a tuple of the database column names to be written to"""
        return (
            "movie_id",
            "original_title",
            "french_title",
            "tagline",
            "rating",
            "runtime",
            "synopsis",
            "cast",
            "languages",
            "genres",
            "release_date",
            "origin_country",
            "imdb_url",
            "poster_hi_res",
            "poster_lo_res",
            "tmdb_id",
            "original_language",
            "spoken_languages",
        )

    def database_format(self):
        """Return object in a format to be inserted into database"""
        return {attr: self.__dict__.get(attr) for attr in self.get_columns()}

    def __str__(self) -> str:
        """Return a string representation of the Movie object."""
        return f"IMDB Ref: {self.imdb_url} \nMovie ID: {self.movie_id} \nOriginal Title: {self.original_title} \nFrench Title: {self.french_title} \nRating: {self.rating} \nRuntime: {self.runtime} \nSynopsis:{self.synopsis} \nCast: {self.cast} \nLanguages: {self.languages} \nGenre(s): {self.genres} \nRelease Date: {self.release_date}"

    def __repr__(self) -> str:
        """Return a string representation of the Movie object for debugging."""
        return f"Movie('{self.imdb_url}', '{self.movie_id}', '{self.original_title}', '{self.french_title}', '{self.rating}', '{self.runtime}', '{self.synopsis}', {self.cast}, {self.languages}, {self.genres}, {self.release_date})"

    def movie_name(self):
        """Return the original title of the movie."""
        return f"Name: {self.original_title}"


class MovieManager:
    def __init__(self, logger: Logger) -> None:
        """Initialize a MovieManager object."""
        self.logger = logger
        self.current_movie_ids = set(self.retrieve_movies())  # type: ignore[call-arg]
        self.new_movies = []

    @connect_to_database
    def retrieve_movies(self, db, cursor) -> list[tuple[str]]:
        """Retrieve existing movie IDs from the database."""
        try:
            query = f"SELECT movie_id FROM {TABLE_NAME};"
            cursor.execute(query)
            results = cursor.fetchall()

            # Convert list of tuples to list of strings
            return [result[0] for result in results]

        except Exception as e:
            self.logger.critical(
                f"MovieManager.retrieve_movies: An error occurred: {str(e)}",
                exc_info=True,
            )
            raise e

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
            try:
                new_movie = self.create_movie(item)
                if new_movie is not None:
                    self.add_new_movie(new_movie)
            except Exception as e:
                self.logger.error(f"Unable to create Movie: {e}")

    def create_movie(self, item: dict) -> Movie | None:
        """Create a Movie object from raw JSON data."""
        try:
            movie_details = {
                "movie_id": item["movie"]["id"],
                "original_title": item["movie"]["originalTitle"].strip(),
                "french_title": item["movie"]["title"].strip(),
                "genres": [
                    genre["tag"].replace("_", " ").title()
                    for genre in item["movie"]["genres"]
                    if genre["tag"] is not None
                ],
                "languages": [
                    language.title()
                    for language in item["movie"]["languages"]
                    if language is not None
                ],
                "cast": self.get_cast(item["movie"]["cast"]["edges"]),
                "release_date": self.get_release_date(item),
            }
            new_movie = Movie(**movie_details, logger=self.logger)

            return new_movie

        except Exception as e:
            self.logger.error(f"Movie could not be created: {e}, raw json data: {item}")

    @staticmethod
    def get_cast(cast_json):
        """Method to extract cast names from scraped json"""
        cast = []
        for cast_raw in cast_json:
            try:
                # Below is to deal with some cast members having only first or last name
                cast_member = cast_raw["node"]["actor"]
                first_name = cast_member["firstName"] or ""
                last_name = cast_member["lastName"] or ""
                name = " ".join([first_name, last_name]).strip()

                cast.append(name)

            except:
                continue
        return cast

    @staticmethod
    def get_release_date(item):
        try:
            date_str = str(item["movie"]["data"]["productionYear"]) + ("-01-01")
            release_date = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            release_date = None
        return release_date

    @connect_to_database
    def add_new_movies_to_database(self, db=None, cursor=None) -> None:
        """Add new movies to the database."""
        if self.new_movies:
            movie_values_list = [movie.database_format() for movie in self.new_movies]

            for movie in self.new_movies:
                self.logger.info(f"Adding new movie to database: \n{movie}")

            columns = Movie.get_columns()
            placeholders = ", ".join(f"%({key})s" for key in columns)
            insert_query = f"INSERT IGNORE INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders});"
            cursor.executemany(insert_query, movie_values_list)
            db.commit()

            # Check for warnings during INSERT IGNORE
            cursor.execute("SHOW WARNINGS;")
            warnings = cursor.fetchall()
            if warnings:
                self.logger.warning(f"Errors during movie insert: {warnings}")

    def __str__(self):
        """Return a string representation of the MovieManager object."""
        if self.new_movies:
            return f"{len(self.new_movies)} new movie(s) found:\n" + "\n".join(
                [movie.movie_name() for movie in self.new_movies]
            )
        else:
            return "No new movies found."
