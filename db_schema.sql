-- Create movies table with auto-incremented integer for movie_id
CREATE TABLE movies (
    movie_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    allocine_id VARCHAR(32),
    original_title VARCHAR(191),
    french_title VARCHAR(191),
    image_poster VARCHAR(255),
    runtime VARCHAR(16),
    synopsis VARCHAR(1000),
    cast VARCHAR(191),
    languages VARCHAR(191),
    genres VARCHAR(191),
    release_date DATE
);

-- Create cinemas table
CREATE TABLE cinemas (
    cinema_id CHAR(5) PRIMARY KEY,
    name VARCHAR(191),
    address VARCHAR(255),
    info VARCHAR(255),
    gps POINT
);

-- Create showtimes table
CREATE TABLE showtimes (
    showtime_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    movie_id INT UNSIGNED,
    cinema_id CHAR(5),
    start_time DATETIME,
    CONSTRAINT fk_movie_id FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    CONSTRAINT fk_cinema_id FOREIGN KEY (cinema_id) REFERENCES cinemas(cinema_id)
);
