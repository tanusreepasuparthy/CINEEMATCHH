import mysql.connector

from mysql.connector import Error


# ==================================
# DATABASE CONFIGURATION
# ==================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "movie_rating_db",
    "port": 3306
}


# ==================================
# DATABASE CONNECTION
# ==================================

def get_connection():

    try:

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        return connection

    except Error as error:

        raise RuntimeError(
            f"MySQL connection failed: {error}"
        ) from error


# ==================================
# TEST DATABASE CONNECTION
# ==================================

def test_connection():

    connection = get_connection()

    try:

        if connection.is_connected():
            return True

        return False

    finally:

        connection.close()