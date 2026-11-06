CREATE DATABASE IF NOT EXISTS movie_rating_db;

USE movie_rating_db;


-- 1. MOVIES TABLE

CREATE TABLE IF NOT EXISTS movies (

    movie_id INT PRIMARY KEY,

    title VARCHAR(255) NOT NULL,

    release_year INT NULL,

    genre VARCHAR(500) NOT NULL

);


-- 2. USERS TABLE

CREATE TABLE IF NOT EXISTS users (

    user_id INT PRIMARY KEY,

    display_name VARCHAR(100) NULL

);


-- 3. RATINGS TABLE

CREATE TABLE IF NOT EXISTS ratings (

    rating_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    movie_id INT NOT NULL,

    rating DECIMAL(2,1) NOT NULL,

    rated_at DATETIME NULL,

    CONSTRAINT fk_rating_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_rating_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_user_movie
        UNIQUE (user_id, movie_id),

    CONSTRAINT chk_rating
        CHECK (rating >= 0.5 AND rating <= 5.0)

);


-- INDEXES FOR FASTER SEARCHING

CREATE INDEX idx_movie_genre
ON movies(genre);

CREATE INDEX idx_rating_movie
ON ratings(movie_id);

CREATE INDEX idx_rating_user
ON ratings(user_id);