import pandas as pd
import numpy as np


# ==================================
# MOVIE RATING STATISTICS
# ==================================

def calculate_movie_statistics(movies, ratings):

    if ratings.empty:
        return pd.DataFrame(
            columns=[
                "movie_id",
                "title",
                "genre",
                "average_rating",
                "rating_count",
                "weighted_rating"
            ]
        )

    statistics = ratings.groupby(
        "movie_id"
    ).agg(
        average_rating=("rating", "mean"),
        rating_count=("rating", "count")
    ).reset_index()

    statistics = statistics.merge(
        movies[
            ["movie_id", "title", "genre"]
        ],
        on="movie_id",
        how="left"
    )

    overall_average = float(
        ratings["rating"].mean()
    )

    # Minimum rating count
    minimum_count = 20

    statistics["weighted_rating"] = (
        (
            statistics["rating_count"]
            /
            (
                statistics["rating_count"]
                + minimum_count
            )
        )
        * statistics["average_rating"]
        +
        (
            minimum_count
            /
            (
                statistics["rating_count"]
                + minimum_count
            )
        )
        * overall_average
    )

    return statistics.sort_values(
        "weighted_rating",
        ascending=False
    )


# ==================================
# TOP RATED MOVIES
# ==================================

def get_top_rated_movies(
    statistics,
    minimum_count=20,
    limit=10
):

    if minimum_count < 1 or limit < 1:
        raise ValueError(
            "Minimum count and limit must be positive."
        )

    result = statistics[
        statistics["rating_count"] >= minimum_count
    ]

    return result.sort_values(
        ["weighted_rating", "rating_count"],
        ascending=False
    ).head(limit).reset_index(drop=True)


# ==================================
# POPULAR MOVIES
# ==================================

def get_popular_movies(
    statistics,
    minimum_count=20,
    limit=10
):

    if minimum_count < 1 or limit < 1:
        raise ValueError(
            "Minimum count and limit must be positive."
        )

    result = statistics[
        statistics["rating_count"] >= minimum_count
    ]

    return result.sort_values(
        ["rating_count", "weighted_rating"],
        ascending=False
    ).head(limit).reset_index(drop=True)


# ==================================
# GENRE ANALYSIS
# ==================================

def get_genre_statistics(movies):

    if movies.empty:
        return pd.Series(dtype="int64")

    genre_data = movies[
        ["movie_id", "genre"]
    ].copy()

    genre_data["genre"] = (
        genre_data["genre"]
        .fillna("")
        .astype(str)
        .str.split("|")
    )

    genre_data = genre_data.explode("genre")

    genre_data["genre"] = (
        genre_data["genre"].str.strip()
    )

    genre_data = genre_data[
        (genre_data["genre"] != "")
        &
        (genre_data["genre"] != "(no genres listed)")
    ]

    return genre_data.groupby(
        "genre"
    )["movie_id"].nunique().sort_values(
        ascending=False
    )


# ==================================
# RATING DISTRIBUTION
# ==================================

def get_rating_distribution(ratings):

    if ratings.empty:
        return pd.Series(dtype="int64")

    return ratings["rating"].value_counts(
        sort=False
    ).sort_index()


# ==================================
# USER ACTIVITY (AGGREGATED ONLY)
# ==================================

def get_user_statistics(ratings):

    if ratings.empty:
        return pd.DataFrame(
            columns=["total_ratings", "average_rating"]
        )

    return ratings.groupby(
        "user_id"
    ).agg(
        total_ratings=("rating", "count"),
        average_rating=("rating", "mean")
    ).reset_index()


# ==================================
# NUMPY STATISTICS
# ==================================

def get_rating_summary(ratings):

    if ratings.empty:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "minimum": 0.0,
            "maximum": 0.0
        }

    values = ratings["rating"].to_numpy(
        dtype=float
    )

    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values)),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values))
    }