"""Tests for the DataStore data loading module."""

import pytest

from app.data.loader import DataStore


# Use a module-scoped fixture so DataStore loads once for all tests
@pytest.fixture(scope="module")
def data_store() -> DataStore:
    """Load the real MovieLens data (requires data/*.parquet to exist)."""
    return DataStore(data_dir="../data")


class TestDataFrameLoading:
    """Verify all three DataFrames load with expected shapes and columns."""

    def test_movies_df_loads(self, data_store: DataStore):
        df = data_store.movies_df
        assert len(df) == 1682
        assert list(df.columns) == ["movie_id", "title", "genres", "year"]

    def test_ratings_df_loads(self, data_store: DataStore):
        df = data_store.ratings_df
        assert len(df) == 100_000
        assert list(df.columns) == ["user_id", "movie_id", "rating", "timestamp"]

    def test_users_df_loads(self, data_store: DataStore):
        df = data_store.users_df
        assert len(df) == 943
        assert list(df.columns) == ["user_id", "age", "gender", "occupation", "zip_code"]


class TestMovieLookup:
    """Verify single-movie lookup by ID."""

    def test_get_movie_returns_toy_story(self, data_store: DataStore):
        movie = data_store.get_movie(1)
        assert movie is not None
        assert "Toy Story" in movie["title"]
        assert movie["year"] == 1995
        assert "Animation" in movie["genres"]

    def test_get_movie_returns_none_for_invalid_id(self, data_store: DataStore):
        assert data_store.get_movie(999999) is None


class TestMovieSearch:
    """Verify case-insensitive substring search on titles."""

    def test_search_toy_story(self, data_store: DataStore):
        results = data_store.search_movies("toy story")
        assert len(results) >= 1
        assert any("Toy Story" in r["title"] for r in results)

    def test_search_case_insensitive(self, data_store: DataStore):
        lower = data_store.search_movies("star wars")
        upper = data_store.search_movies("STAR WARS")
        assert len(lower) == len(upper)

    def test_search_respects_limit(self, data_store: DataStore):
        results = data_store.search_movies("the", limit=5)
        assert len(results) <= 5

    def test_search_empty_query_returns_empty(self, data_store: DataStore):
        assert data_store.search_movies("") == []
        assert data_store.search_movies("   ") == []

    def test_search_no_match_returns_empty(self, data_store: DataStore):
        results = data_store.search_movies("xyznonexistentmovie")
        assert results == []


class TestEligibleGroundTruthUsers:
    """Verify ground-truth user selection logic."""

    def test_returns_nonempty_list(self, data_store: DataStore):
        eligible = data_store.get_eligible_ground_truth_users()
        assert len(eligible) > 0

    def test_eligible_users_are_sorted(self, data_store: DataStore):
        eligible = data_store.get_eligible_ground_truth_users()
        assert eligible == sorted(eligible)

    def test_stricter_criteria_reduces_pool(self, data_store: DataStore):
        loose = data_store.get_eligible_ground_truth_users(min_genres=2, min_ratings=10)
        strict = data_store.get_eligible_ground_truth_users(min_genres=5, min_ratings=50)
        assert len(strict) <= len(loose)

    def test_eligible_users_are_valid_user_ids(self, data_store: DataStore):
        eligible = data_store.get_eligible_ground_truth_users()
        valid_ids = set(data_store.users_df["user_id"])
        for uid in eligible:
            assert uid in valid_ids
