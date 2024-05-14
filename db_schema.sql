-- Create movies table with auto-incremented integer for movie_id
CREATE TABLE movies (
    movie_id VARCHAR(191) PRIMARY KEY,
    original_title VARCHAR(191),
    french_title VARCHAR(191),
    rating FLOAT,
    runtime SMALLINT UNSIGNED,
    synopsis VARCHAR(1000),
    cast VARCHAR(191),
    languages VARCHAR(191),
    genres VARCHAR(191),
    release_date DATE,
    homepage VARCHAR(255),
    imdb_url VARCHAR(255),
    origin_country VARCHAR(191),
    poster_hi_res VARCHAR(255),
    poster_lo_res VARCHAR(255),
    tagline VARCHAR(255),
    tmdb_id INT UNSIGNED,

);

-- Create cinemas table
CREATE TABLE cinemas (
    cinema_id CHAR(5) PRIMARY KEY,
    `name` VARCHAR(191),
    `address` VARCHAR(255),
    info VARCHAR(255),
    gps POINT,
    town VARCHAR(191)
);

-- Create showtimes table
-- hash_id is used to compare showings in database with newly scrapes showings to identify unknown ones, using SHA256
CREATE TABLE showtimes (
    showtime_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    movie_id CHAR(16),
    cinema_id CHAR(5),
    start_time DATETIME,
    hash_id CHAR(64),
    CONSTRAINT fk_movie_id FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    CONSTRAINT fk_cinema_id FOREIGN KEY (cinema_id) REFERENCES cinemas(cinema_id),
    CONSTRAINT unique_hash_id UNIQUE (hash_id)
);
