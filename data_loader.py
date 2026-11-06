import pandas as pd

from src.database import get_connection


# ==================================
# LOAD MOVIES
# ==================================

def load_movies():

    connection = get_connection()

    try:

        query = """
            SELECT
                movie_id,
                title,
                release_year,
                genre
            FROM movies
            ORDER BY title
        """

        return pd.read_sql(
            query,
            connection
        )

    finally:

        connection.close()


# ==================================
# LOAD RATINGS
# ==================================

def load_ratings():

    connection = get_connection()

    try:

        query = """
            SELECT
                rating_id,
                user_id,
                movie_id,
                rating,
                rated_at
            FROM ratings
        """

        return pd.read_sql(
            query,
            connection
        )

    finally:

        connection.close()


# ==================================
# LOAD COMBINED DATA
# ==================================

def load_combined_data():

    connection = get_connection()

    try:

        query = """
            SELECT
                m.movie_id,
                m.title,
                m.release_year,
                m.genre,
                r.user_id,
                r.rating,
                r.rated_at

            FROM movies m

            INNER JOIN ratings r
                ON m.movie_id = r.movie_id
        """

        return pd.read_sql(
            query,
            connection
        )

    finally:

        connection.close()