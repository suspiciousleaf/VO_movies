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
        "cinemas": """CREATE TABLE IF NOT EXISTS `cinemas` (
                    `cinema_id` CHAR(5) PRIMARY KEY,
                    `name` VARCHAR(191) DEFAULT NULL,
                    `address` VARCHAR(255) DEFAULT NULL,
                    `info` VARCHAR(255) DEFAULT NULL,
                    `gps` POINT DEFAULT NULL,
                    `town` VARCHAR(191) DEFAULT NULL,
                    `department` VARCHAR(191) DEFAULT NULL
                );""",
        "movies": """CREATE TABLE IF NOT EXISTS `movies` (
                    `movie_id` VARCHAR(191) PRIMARY KEY,
                    `original_title` VARCHAR(191) DEFAULT NULL,
                    `french_title` VARCHAR(191) DEFAULT NULL,
                    `rating` FLOAT DEFAULT NULL,
                    `runtime` SMALLINT UNSIGNED DEFAULT NULL,
                    `synopsis` VARCHAR(1000) DEFAULT NULL,
                    `cast` VARCHAR(191) DEFAULT NULL,
                    `languages` VARCHAR(191) DEFAULT NULL,
                    `genres` VARCHAR(191) DEFAULT NULL,
                    `release_date` DATE DEFAULT NULL,
                    `imdb_url` VARCHAR(255) DEFAULT NULL,
                    `origin_country` VARCHAR(191) DEFAULT NULL,
                    `poster_hi_res` VARCHAR(255) DEFAULT NULL,
                    `poster_lo_res` VARCHAR(255) DEFAULT NULL,
                    `tagline` VARCHAR(255) DEFAULT NULL,
                    `tmdb_id` INT UNSIGNED DEFAULT NULL,
                    `rating_imdb` TINYINT UNSIGNED DEFAULT NULL,
                    `rating_rt` TINYINT UNSIGNED DEFAULT NULL,
                    `rating_meta` TINYINT UNSIGNED DEFAULT NULL,
                    `date_added` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
                );""",
        "showtimes": """CREATE TABLE IF NOT EXISTS `showtimes` (
                    `showtime_id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
                    `movie_id` VARCHAR(191) DEFAULT NULL,
                    `cinema_id` CHAR(5) DEFAULT NULL,
                    `start_time` DATETIME DEFAULT NULL,
                    `hash_id` CHAR(64) DEFAULT NULL,
                    UNIQUE KEY `unique_hash_id` (`hash_id`),
                    KEY `startime_idx` (`start_time`),
                    KEY `fk_movie_id` (`movie_id`),
                    KEY `fk_cinema_id` (`cinema_id`),
                    CONSTRAINT `fk_movie_id` FOREIGN KEY (`movie_id`) REFERENCES `movies` (`movie_id`),
                    CONSTRAINT `fk_cinema_id` FOREIGN KEY (`cinema_id`) REFERENCES `cinemas` (`cinema_id`)
                );""",
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
