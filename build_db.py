from db_utilities import connect_to_database
from data.cinema_info import cinema_data


def create_tables(db, cursor, logger):
    """Create necessary tables in the database if they do not exist."""
    tables_query = "SHOW TABLES;"
    cursor.execute(tables_query)
    tables_present = cursor.fetchall()
    if tables_present is not None:
        tables_present = set(table[0] for table in tables_present)

    queries = {
        "movies": "CREATE TABLE movies (movie_id VARCHAR(191) PRIMARY KEY,original_title VARCHAR(191),french_title VARCHAR(191),runtime SMALLINT UNSIGNED,synopsis VARCHAR(1000),cast VARCHAR(191),languages VARCHAR(191),genres VARCHAR(191),release_date DATE,imdb_url VARCHAR(255),origin_country VARCHAR(191),poster_hi_res VARCHAR(255),poster_lo_res VARCHAR(255),tagline VARCHAR(255),tmdb_id INT UNSIGNED,rating_imdb TINYINT UNSIGNED,rating_rt TINYINT UNSIGNED,rating_meta TINYINT UNSIGNED,date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP););",
        "cinemas": "CREATE TABLE cinemas (cinema_id CHAR(5) PRIMARY KEY,`name` VARCHAR(191),`address` VARCHAR(255),info VARCHAR(255),gps POINT,town VARCHAR(191));",
        "showtimes": "CREATE TABLE showtimes (showtime_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,movie_id VARCHAR(191),cinema_id CHAR(5),start_time DATETIME,hash_id CHAR(64),CONSTRAINT fk_movie_id FOREIGN KEY (movie_id) REFERENCES movies(movie_id),CONSTRAINT fk_cinema_id FOREIGN KEY (cinema_id) REFERENCES cinemas(cinema_id),CONSTRAINT unique_hash_id UNIQUE (hash_id));",
    }

    for query in queries:
        if query not in tables_present:
            cursor.execute(queries[query])
            logger.info(f"Table {query} created")
            tables_present.add(query)
        else:
            logger.info(f"Table {query} already exists")

    return tables_present


def add_cinemas(db, cursor, logger):
    """Add cinema records to the cinemas table in the database."""

    cinema_ids_query = "SELECT cinema_id FROM cinemas;"
    cursor.execute(cinema_ids_query)
    results = cursor.fetchall()
    if results is not None:
        current_cinema_ids = [result[0] for result in results]

    cinema_data_to_add = [
        cinema for cinema in cinema_data if cinema[0] not in current_cinema_ids
    ]

    query = """
        INSERT INTO cinemas (cinema_id, `name`, `address`, info, gps, town) 
        VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s);
    """

    cursor.executemany(query, cinema_data_to_add)
    db.commit()
    logger.info(f"{len(cinema_data_to_add)} cinema(s) added to database")


@connect_to_database
def build_db(db, cursor, logger):
    """Initialize the database by creating tables and adding cinema data."""
    tables_present = create_tables(db, cursor, logger=logger)
    add_cinemas(db, cursor, logger=logger)
    return f"Tables in databse: {tables_present}"
