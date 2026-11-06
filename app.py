import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.database import get_connection, test_connection

from src.data_loader import (
    load_movies,
    load_ratings,
    load_combined_data
)

from src.analysis import (
    calculate_movie_statistics,
    get_top_rated_movies,
    get_popular_movies,
    get_genre_statistics,
    get_rating_distribution,
    get_rating_summary
)

from src.recommendation import (
    popularity_recommendations,
    similarity_recommendations
)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Movie Rating Analysis",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Rating Analysis")

st.caption(
    "Movie Analytics and Basic Recommendation System"
)

sns.set_theme(style="whitegrid")


# ==========================================
# DATABASE CHECK
# ==========================================

try:

    if not test_connection():
        st.error("MySQL connection is unavailable.")
        st.stop()

except Exception as error:

    st.error(f"Database connection error: {error}")

    st.stop()


# ==========================================
# LOAD DATA
# ==========================================

try:

    movies = load_movies()

    ratings = load_ratings()

    combined_data = load_combined_data()

except Exception as error:

    st.error(f"Unable to load data: {error}")

    st.stop()


# ==========================================
# CALCULATE STATISTICS
# ==========================================

statistics = calculate_movie_statistics(
    movies,
    ratings
)


# ==========================================
# NAVIGATION
# ==========================================

st.sidebar.title("🎬 Movie System")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Manage Movies",
        "Manage Ratings",
        "Movie Analysis",
        "Genre Analysis",
        "Recommendations"
    ]
)


# ==========================================
# DATABASE INSERT FUNCTION
# ==========================================

def execute_insert(query, values):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(query, values)

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        cursor.close()

        connection.close()


# ==========================================
# 1. DASHBOARD
# ==========================================

if page == "Dashboard":

    st.header("Project Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Movies",
        f"{movies['movie_id'].nunique():,}"
    )

    col2.metric(
        "Total Ratings",
        f"{len(ratings):,}"
    )

    col3.metric(
        "Total Users",
        f"{ratings['user_id'].nunique():,}"
    )

    average = (
        ratings["rating"].mean()
        if not ratings.empty else 0
    )

    col4.metric(
        "Average Rating",
        f"{average:.2f}/5"
    )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader("Rating Distribution")

        if not ratings.empty:

            fig, ax = plt.subplots(figsize=(8, 4))

            sns.histplot(
                data=ratings,
                x="rating",
                bins=10,
                ax=ax
            )

            ax.set_xlabel("Rating")

            ax.set_ylabel("Number of Ratings")

            st.pyplot(fig)

            plt.close(fig)

        else:

            st.info("No ratings available.")

    with right:

        st.subheader("Genre Distribution")

        genre_counts = get_genre_statistics(movies)

        if not genre_counts.empty:

            fig, ax = plt.subplots(figsize=(8, 4))

            genre_counts.head(10).sort_values().plot(
                kind="barh",
                ax=ax
            )

            ax.set_xlabel("Number of Movies")

            ax.set_ylabel("Genre")

            st.pyplot(fig)

            plt.close(fig)

        else:

            st.info("No genre information available.")

    st.subheader("Top Rated Movies")

    top_movies = get_top_rated_movies(
        statistics,
        minimum_count=20,
        limit=10
    )

    st.dataframe(
        top_movies[
            [
                "title",
                "average_rating",
                "rating_count",
                "weighted_rating"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 2. MANAGE MOVIES
# ==========================================

elif page == "Manage Movies":

    st.header("Manage Movies")

    st.subheader("Add a New Movie")

    with st.form("movie_form"):

        title = st.text_input("Movie Title")

        release_year = st.number_input(
            "Release Year",
            min_value=1888,
            max_value=2100,
            value=2020
        )

        genre = st.text_input(
            "Genres",
            placeholder="Action|Drama|Comedy"
        )

        submitted = st.form_submit_button(
            "Add Movie"
        )

        if submitted:

            if not title.strip():

                st.error("Movie title is required.")

            elif not genre.strip():

                st.error("At least one genre is required.")

            else:

                try:

                    connection = get_connection()

                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT COALESCE(MAX(movie_id), 0) + 1
                        FROM movies
                        """
                    )

                    new_id = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO movies
                        (movie_id, title, release_year, genre)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            new_id,
                            title.strip(),
                            int(release_year),
                            genre.strip()
                        )
                    )

                    connection.commit()

                    st.success("Movie added successfully!")

                    st.rerun()

                except Exception as error:

                    st.error(f"Unable to add movie: {error}")

                finally:

                    if "cursor" in locals():
                        cursor.close()

                    if "connection" in locals():
                        connection.close()

    st.divider()

    st.subheader("Available Movies")

    st.dataframe(
        movies,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 3. MANAGE RATINGS
# ==========================================

elif page == "Manage Ratings":

    st.header("Manage Ratings")

    st.subheader("Add a Movie Rating")

    with st.form("rating_form"):

        user_id = st.number_input(
            "User ID",
            min_value=1,
            step=1
        )

        movie_options = movies[
            ["movie_id", "title"]
        ].to_dict("records")

        selected_movie = st.selectbox(
            "Select Movie",
            movie_options,
            format_func=lambda x: x["title"]
        )

        rating = st.select_slider(
            "Give Rating",
            options=[
                0.5, 1.0, 1.5, 2.0, 2.5,
                3.0, 3.5, 4.0, 4.5, 5.0
            ],
            value=4.0
        )

        submitted = st.form_submit_button(
            "Submit Rating"
        )

        if submitted:

            try:

                connection = get_connection()

                cursor = connection.cursor()

                # Create user if not already present
                cursor.execute(
                    """
                    INSERT IGNORE INTO users
                    (user_id, display_name)
                    VALUES (%s, NULL)
                    """,
                    (int(user_id),)
                )

                # Insert or update the user's rating
                cursor.execute(
                    """
                    INSERT INTO ratings
                    (user_id, movie_id, rating, rated_at)

                    VALUES (%s, %s, %s, NOW())

                    ON DUPLICATE KEY UPDATE
                        rating = VALUES(rating),
                        rated_at = VALUES(rated_at)
                    """,
                    (
                        int(user_id),
                        selected_movie["movie_id"],
                        float(rating)
                    )
                )

                connection.commit()

                st.success(
                    "Rating submitted successfully!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Unable to submit rating: {error}"
                )

            finally:

                if "cursor" in locals():
                    cursor.close()

                if "connection" in locals():
                    connection.close()

    st.divider()

    st.subheader("Rating Summary")

    st.write(
        "Only aggregate statistics are displayed here. "
        "Individual users' rating histories are not exposed."
    )

    st.metric(
        "Total Ratings",
        len(ratings)
    )


# ==========================================
# 4. MOVIE ANALYSIS
# ==========================================

elif page == "Movie Analysis":

    st.header("Movie Rating Analysis")

    minimum_count = st.slider(
        "Minimum number of ratings",
        min_value=1,
        max_value=100,
        value=20
    )

    summary = get_rating_summary(ratings)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean Rating",
        f"{summary['mean']:.2f}"
    )

    col2.metric(
        "Median Rating",
        f"{summary['median']:.2f}"
    )

    col3.metric(
        "Standard Deviation",
        f"{summary['std']:.2f}"
    )

    st.subheader("Top Rated Movies")

    top_movies = get_top_rated_movies(
        statistics,
        minimum_count=minimum_count,
        limit=20
    )

    st.dataframe(
        top_movies,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Most Popular Movies")

    popular_movies = get_popular_movies(
        statistics,
        minimum_count=minimum_count,
        limit=20
    )

    st.dataframe(
        popular_movies,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 5. GENRE ANALYSIS
# ==========================================

elif page == "Genre Analysis":

    st.header("Genre Analysis")

    genre_counts = get_genre_statistics(movies)

    if genre_counts.empty:

        st.warning("No genre data available.")

    else:

        st.subheader("Movies by Genre")

        genre_df = genre_counts.rename_axis(
            "Genre"
        ).reset_index(
            name="Movie Count"
        )

        st.dataframe(
            genre_df,
            use_container_width=True,
            hide_index=True
        )

        fig, ax = plt.subplots(figsize=(10, 6))

        genre_counts.sort_values().plot(
            kind="barh",
            ax=ax
        )

        ax.set_title("Genre Distribution")

        ax.set_xlabel("Number of Movies")

        ax.set_ylabel("Genre")

        st.pyplot(fig)

        plt.close(fig)


# ==========================================
# 6. RECOMMENDATIONS
# ==========================================

elif page == "Recommendations":

    st.header("Movie Recommendation System")

    method = st.radio(
        "Choose Recommendation Method",
        [
            "Popularity Based",
            "Genre Similarity"
        ]
    )

    if method == "Popularity Based":

        st.write(
            "Recommendations are ranked using weighted "
            "ratings and rating counts."
        )

        minimum_count = st.number_input(
            "Minimum Rating Count",
            min_value=1,
            max_value=1000,
            value=20
        )

        limit = st.slider(
            "Number of Recommendations",
            5, 20, 10
        )

        if st.button("Get Popular Recommendations"):

            result = popularity_recommendations(
                statistics,
                minimum_count=int(minimum_count),
                limit=limit
            )

            if result.empty:

                st.warning(
                    "No movies satisfy the minimum rating count."
                )

            else:

                st.success(
                    "Popular recommendations generated."
                )

                st.dataframe(
                    result[
                        [
                            "title",
                            "genre",
                            "average_rating",
                            "rating_count",
                            "weighted_rating"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )

    else:

        st.write(
            "Recommendations are based on genre similarity."
        )

        if movies.empty:

            st.warning("No movies available.")

        else:

            movie_options = movies[
                ["movie_id", "title"]
            ].to_dict("records")

            selected = st.selectbox(
                "Select a movie",
                movie_options,
                format_func=lambda x: x["title"]
            )

            limit = st.slider(
                "Number of Similar Movies",
                5, 20, 10
            )

            if st.button("Find Similar Movies"):

                result = similarity_recommendations(
                    movies,
                    selected["movie_id"],
                    limit
                )

                if result.empty:

                    st.warning(
                        "No similar movies were found."
                    )

                else:

                    st.success(
                        "Similar movies generated successfully."
                    )

                    st.dataframe(
                        result[
                            [
                                "title",
                                "release_year",
                                "genre",
                                "similarity_score"
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Movie Rating Analysis and Basic Recommendation System"
)

st.caption(
    "Python | MySQL | Pandas | NumPy | Matplotlib | Streamlit"
)