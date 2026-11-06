import pandas as pd

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity


# ==================================
# POPULARITY RECOMMENDATIONS
# ==================================

def popularity_recommendations(
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
    ].copy()

    result = result.sort_values(
        ["weighted_rating", "rating_count"],
        ascending=False
    )

    return result.head(limit).reset_index(drop=True)


# ==================================
# GENRE SIMILARITY RECOMMENDATIONS
# ==================================

def similarity_recommendations(
    movies,
    selected_movie_id,
    limit=10
):

    if limit < 1:
        raise ValueError(
            "Limit must be positive."
        )

    if movies.empty:
        return pd.DataFrame()

    if selected_movie_id not in movies["movie_id"].values:
        raise ValueError(
            "Selected movie does not exist."
        )

    movie_data = movies.reset_index(drop=True).copy()

    # Convert genres into lists
    genre_lists = movie_data["genre"].fillna("").apply(
        lambda value: [
            genre.strip()
            for genre in str(value).split("|")
            if genre.strip()
            and genre.strip() != "(no genres listed)"
        ]
    )

    # Find selected movie
    selected_index = movie_data.index[
        movie_data["movie_id"] == selected_movie_id
    ][0]

    # Check whether selected movie has genres
    if not genre_lists.iloc[selected_index]:
        return pd.DataFrame()

    # Convert genres into numerical features
    encoder = MultiLabelBinarizer()

    genre_matrix = encoder.fit_transform(
        genre_lists
    )

    # Calculate cosine similarity
    similarity_matrix = cosine_similarity(
        genre_matrix
    )

    scores = similarity_matrix[selected_index]

    # Create recommendation results
    result = movie_data[
        ["movie_id", "title", "release_year", "genre"]
    ].copy()

    result["similarity_score"] = scores

    # Remove the selected movie
    result = result[
        result["movie_id"] != selected_movie_id
    ]

    # Remove zero similarity
    result = result[
        result["similarity_score"] > 0
    ]

    result = result.sort_values(
        "similarity_score",
        ascending=False
    )

    return result.head(limit).reset_index(drop=True)