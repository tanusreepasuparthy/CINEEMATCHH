from pathlib import Path
import re

import pandas as pd

from src.database import get_connection


BASE_DIR = Path(__file__).resolve().parent

MOVIES_FILE = BASE_DIR / "data" / "movies.csv"

RATINGS_FILE = BASE_DIR / "data" / "ratings.csv"


# ==================================
# READ DATASETS
# ==================================

def read_datasets():

    if not MOVIES_FILE.exists():
        raise FileNotFoundError(
            f"Movies file not found: {MOVIES_FILE}"
        )

    if not RATINGS_FILE.exists():
        raise FileNotFoundError(
            f"Ratings file not found: {RATINGS_FILE}"
        )

    movies = pd.read_csv(MOVIES_FILE)

    ratings = pd.read_csv(RATINGS_FILE)

    required_movies = {
        "movieId", "title", "genres"
    }

    required_ratings = {
        "userId", "movieId", "rating", "timestamp"
    }

    if not required_movies.issubset(movies.columns):
        raise ValueError(
            "Invalid movies.csv columns."
        )

    if not required_ratings.issubset(ratings.columns):
        raise ValueError(
            "Invalid ratings.csv columns."
        )

    return movies, ratings


# ==================================
# CLEAN MOVIES
# ==================================

def clean_movies(movies):

    movies = movies.copy()

    movies["movieId"] = pd.to_numeric(
        movies["movieId"],
        errors="coerce"
    )

    movies = movies.dropna(
        subset=["movieId", "title"]
    )

    movies["title"] = movies["title"].astype(str).str.strip()

    movies["genres"] = (
        movies["genres"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    movies = movies.drop_duplicates(
        subset=["movieId"]
    )

    movies["movieId"] = movies["movieId"].astype(int)

    # Extract release year from movie title
    def extract_year(title):

        match = re.search(
            r"\((\d{4})\)\s*$",
            title
        )

        if match:
            return int(match.group(1))

        return None

    movies["release_year"] = movies["title"].apply(
        extract_year
    )

    return movies


# ==================================
# CLEAN RATINGS
# ==================================

def clean_ratings(ratings, valid_movie_ids):

    ratings = ratings.copy()

    for column in ["userId", "movieId", "rating", "timestamp"]:
        ratings[column] = pd.to_numeric(
            ratings[column],
            errors="coerce"
        )

    ratings = ratings.dropna(
        subset=["userId", "movieId", "rating", "timestamp"]
    )

    ratings = ratings[
        ratings["rating"].between(0.5, 5.0)
    ]

    ratings = ratings[
        ratings["movieId"].isin(valid_movie_ids)
    ]

    ratings = ratings.drop_duplicates(
        subset=["userId", "movieId"],
        keep="last"
    )

    ratings["userId"] = ratings["userId"].astype(int)

    ratings["movieId"] = ratings["movieId"].astype(int)

    ratings["timestamp"] = ratings["timestamp"].astype(int)

    ratings["rated_at"] = pd.to_datetime(
        ratings["timestamp"],
        unit="s",
        utc=True
    ).dt.tz_convert(None)

    return ratings


# ==================================
# IMPORT INTO MYSQL
# ==================================

def import_data():

    movies, ratings = read_datasets()

    movies = clean_movies(movies)

    ratings = clean_ratings(
        ratings,
        set(movies["movieId"])
    )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        # Insert movies
        movie_query = """
            INSERT INTO movies
            (movie_id, title, release_year, genre)

            VALUES (%s, %s, %s, %s)

            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                release_year = VALUES(release_year),
                genre = VALUES(genre)
        """

        movie_values = [
            (
                int(row.movieId),
                row.title,
                (
                    int(row.release_year)
                    if pd.notna(row.release_year)
                    else None
                ),
                row.genres
            )
            for row in movies.itertuples(index=False)
        ]

        cursor.executemany(
            movie_query,
            movie_values
        )

        # Insert users
        user_ids = sorted(
            ratings["userId"].unique().tolist()
        )

        user_query = """
            INSERT IGNORE INTO users
            (user_id, display_name)
            VALUES (%s, %s)
        """

        user_values = [
            (int(user_id), None)
            for user_id in user_ids
        ]

        cursor.executemany(
            user_query,
            user_values
        )

        # Insert ratings
        rating_query = """
            INSERT INTO ratings
            (user_id, movie_id, rating, rated_at)

            VALUES (%s, %s, %s, %s)

            ON DUPLICATE KEY UPDATE
                rating = VALUES(rating),
                rated_at = VALUES(rated_at)
        """

        rating_values = [
            (
                int(row.userId),
                int(row.movieId),
                float(row.rating),
                row.rated_at.to_pydatetime()
            )
            for row in ratings.itertuples(index=False)
        ]

        cursor.executemany(
            rating_query,
            rating_values
        )

        connection.commit()

        print("Data imported successfully!")

        print("Movies:", len(movies))

        print("Users:", len(user_ids))

        print("Ratings:", len(ratings))

    except Exception:

        connection.rollback()

        raise

    finally:

        cursor.close()

        connection.close()


if __name__ == "__main__":

    try:

        import_data()

    except Exception as error:

        print("Import failed:", error)