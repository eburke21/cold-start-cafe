"""Data loading and access layer for MovieLens 100K Parquet files."""

from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()


class DataStore:
    """Loads MovieLens 100K Parquet files and provides read-only access.

    Instantiated once at startup and stored on app.state.
    All DataFrames are held in memory for the lifetime of the process.
    """

    def __init__(self, data_dir: str = "data") -> None:
        data_path = Path(data_dir)

        logger.info("Loading MovieLens data", data_dir=str(data_path))
        self._movies_df = pd.read_parquet(data_path / "movies.parquet")
        self._ratings_df = pd.read_parquet(data_path / "ratings.parquet")
        self._users_df = pd.read_parquet(data_path / "users.parquet")

        # Build a movie_id -> row dict for fast O(1) lookups
        self._movie_index: dict[int, dict] = {
            row["movie_id"]: row.to_dict() for _, row in self._movies_df.iterrows()
        }

        logger.info(
            "Data loaded",
            movies=len(self._movies_df),
            ratings=len(self._ratings_df),
            users=len(self._users_df),
        )

    @property
    def movies_df(self) -> pd.DataFrame:
        return self._movies_df

    @property
    def ratings_df(self) -> pd.DataFrame:
        return self._ratings_df

    @property
    def users_df(self) -> pd.DataFrame:
        return self._users_df

    def get_movie(self, movie_id: int) -> dict | None:
        """Look up a single movie by ID. Returns None if not found."""
        return self._movie_index.get(movie_id)

    def search_movies(self, query: str, limit: int = 10) -> list[dict]:
        """Case-insensitive substring search on movie titles."""
        if not query or not query.strip():
            return []
        mask = self._movies_df["title"].str.contains(query, case=False, na=False)
        results = self._movies_df[mask].head(limit)
        return results.to_dict(orient="records")

    def get_eligible_ground_truth_users(
        self, min_genres: int = 3, min_ratings: int = 20
    ) -> list[int]:
        """Find users suitable as ground-truth targets for simulation.

        A user is eligible if they have:
        - At least `min_ratings` total ratings (enough data to evaluate against)
        - Rated movies across at least `min_genres` distinct genres (diverse taste)

        These users make good simulation targets because they have enough
        held-out ratings across enough genres for metrics to be meaningful.
        """
        # Count ratings per user
        user_rating_counts = self._ratings_df.groupby("user_id").size()
        users_with_enough_ratings = set(user_rating_counts[user_rating_counts >= min_ratings].index)

        # Count distinct genres per user
        rated_movies = self._ratings_df[["user_id", "movie_id"]].merge(
            self._movies_df[["movie_id", "genres"]], on="movie_id"
        )
        # Explode pipe-delimited genres into separate rows
        rated_movies["genre"] = rated_movies["genres"].str.split("|")
        exploded = rated_movies.explode("genre")
        user_genre_counts = exploded.groupby("user_id")["genre"].nunique()
        users_with_enough_genres = set(user_genre_counts[user_genre_counts >= min_genres].index)

        eligible = users_with_enough_ratings & users_with_enough_genres
        return sorted(eligible)
