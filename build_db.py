from os import getenv
import json

from db_utilities import connect_to_database
from data.cinema_info import cinema_data

# Environment variables loaded by db_utilities
DB_NAME = getenv("DB_NAME")


@connect_to_database
def test_db_connection(db, cursor, logger):
    """Test if back end can connect to database"""
    try:
        query = "SELECT DATABASE();"
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            current_db = results[0][0]
            if DB_NAME == current_db:
                logger.info("Database connection successful")
                return "Database connection successful"
            else:
                logger.warning(
                    f"Database connection validation failed, expected: {DB_NAME}, got: {current_db}"
                )
                return f"Database connection validation failed, expected: {DB_NAME}, got: {current_db}"
                # return "Database connection failed"
        else:
            logger.error("No results returned from database query")
            return "No results returned from database query"
            # return "Database connection failed"
    except Exception as e:
        logger.error(f"Exception during database connection test: {e}", exc_info=True)
        return f"Exception during database connection test: {e}"
        # return "Database connection failed"


def create_tables(db, cursor, logger):
    """Create tables in new database if not present"""
    tables_query = "SHOW TABLES;"
    cursor.execute(tables_query)
    tables_present = cursor.fetchall()
    if tables_present is not None:
        tables_present = set(table[0] for table in tables_present)

    queries = {
        "movies": "CREATE TABLE movies (movie_id VARCHAR(191) PRIMARY KEY,original_title VARCHAR(191), french_title VARCHAR(191), rating FLOAT,runtime SMALLINT UNSIGNED,synopsis VARCHAR(1000),cast VARCHAR(191),languages VARCHAR(191),genres VARCHAR(191),release_date DATE,imdb_url VARCHAR(255),origin_country VARCHAR(191),poster_hi_res VARCHAR(255),poster_lo_res VARCHAR(255),tagline VARCHAR(255),tmdb_id INT UNSIGNED);",
        "cinemas": "CREATE TABLE cinemas (cinema_id CHAR(5) PRIMARY KEY,`name` VARCHAR(191),`address` VARCHAR(255),info VARCHAR(255),gps POINT,town VARCHAR(191));",
        "showtimes": "CREATE TABLE showtimes (showtime_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,movie_id CHAR(16),cinema_id CHAR(5),start_time DATETIME,hash_id CHAR(64),CONSTRAINT fk_movie_id FOREIGN KEY (movie_id) REFERENCES movies(movie_id),CONSTRAINT fk_cinema_id FOREIGN KEY (cinema_id) REFERENCES cinemas(cinema_id),CONSTRAINT unique_hash_id UNIQUE (hash_id));",
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
    """Add cinemas to new database"""

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
    tables_present = create_tables(db, cursor, logger=logger)
    add_cinemas(db, cursor, logger=logger)
    return f"Tables in databse: {tables_present}"
