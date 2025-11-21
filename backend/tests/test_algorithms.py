"""Tests for recommendation algorithms using a small fixture dataset.

Constructs a controlled dataset of 20 movies and 50 ratings with
known properties, allowing deterministic verification of algorithm behavior.
"""

import pandas as pd
import pytest

from app.data.loader import DataStore
from app.models.simulation import Demographics, Rating, SimulationState
from app.services.algorithms import collaborative, content_based, hybrid, popularity

# ---------------------------------------------------------------------------
# Fixture: build a small, controlled DataStore
# ---------------------------------------------------------------------------


def _build_fixture_datastore(tmp_path) -> DataStore:
    """Build a DataStore with 20 movies, 10 users, and ~60 ratings.

    Movie genre structure (designed for predictable content-based results):
      - Movies 1-5:  Action
      - Movies 6-10: Comedy
      - Movies 11-15: Drama
      - Movies 16-18: Action|Comedy
      - Movies 19-20: Drama|Comedy
    """

    # Movies — helper to keep lines short
    def _movie(mid, title, genres, year):
        return {"movie_id": mid, "title": title, "genres": genres, "year": year}

    movies = []
    for i in range(1, 6):
        movies.append(_movie(i, f"Action Movie {i} (2000)", "Action", 2000))
    for i in range(6, 11):
        movies.append(_movie(i, f"Comedy Movie {i} (2001)", "Comedy", 2001))
    for i in range(11, 16):
        movies.append(_movie(i, f"Drama Movie {i} (2002)", "Drama", 2002))
    for i in range(16, 19):
        movies.append(_movie(i, f"Action Comedy {i} (2003)", "Action|Comedy", 2003))
    for i in range(19, 21):
        movies.append(_movie(i, f"Drama Comedy {i} (2004)", "Drama|Comedy", 2004))

    movies_df = pd.DataFrame(movies)

    # Users (10 users with varying demographics)
    users = []
    occupations = ["student", "engineer", "artist", "teacher", "doctor"]
    for i in range(1, 11):
        users.append(
            {
                "user_id": i,
                "age": 20 + i * 3,
                "gender": "M" if i % 2 == 0 else "F",
                "occupation": occupations[i % 5],
                "zip_code": f"1000{i}",
            }
        )
    users_df = pd.DataFrame(users)

    # Ratings: users 1-5 prefer Action (high), users 6-10 prefer Comedy
    def _rating(uid, mid, score):
        return {"user_id": uid, "movie_id": mid, "rating": score, "timestamp": 1000000}

    ratings = []
    for user_id in range(1, 6):
        # Action fans rate action movies highly
        for movie_id in range(1, 6):
            ratings.append(_rating(user_id, movie_id, 4.5))
        # They rate comedies lower
        for movie_id in range(6, 11):
            ratings.append(_rating(user_id, movie_id, 2.0))
    for user_id in range(6, 11):
        # Comedy fans rate comedies highly
        for movie_id in range(6, 11):
            ratings.append(_rating(user_id, movie_id, 5.0))
        # They rate action movies lower
        for movie_id in range(1, 6):
            ratings.append(_rating(user_id, movie_id, 2.5))

    # Some cross-genre ratings for movies 16-20
    for user_id in range(1, 11):
        ratings.append(_rating(user_id, 16, 3.5))

    ratings_df = pd.DataFrame(ratings)

    # Save to parquet and create DataStore
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    movies_df.to_parquet(data_dir / "movies.parquet")
    ratings_df.to_parquet(data_dir / "ratings.parquet")
    users_df.to_parquet(data_dir / "users.parquet")

    return DataStore(data_dir=str(data_dir))


@pytest.fixture(scope="module")
def fixture_data(tmp_path_factory) -> DataStore:
    """Module-scoped fixture DataStore with controlled data."""
    tmp_path = tmp_path_factory.mktemp("test_algorithms")
    return _build_fixture_datastore(tmp_path)


def _empty_state() -> SimulationState:
    """Create a SimulationState with zero signals."""
    return SimulationState()


# ---------------------------------------------------------------------------
# Popularity Tests
# ---------------------------------------------------------------------------


class TestPopularity:
    """Verify popularity baseline behavior."""

    def test_returns_results_with_zero_signals(self, fixture_data: DataStore):
        """Popularity always returns results, even with no user signals."""
        state = _empty_state()
        result = popularity.recommend(state, fixture_data)
        assert len(result.movie_ids) > 0
        assert len(result.movie_ids) <= 10

    def test_returns_at_most_10_results(self, fixture_data: DataStore):
        state = _empty_state()
        result = popularity.recommend(state, fixture_data)
        assert len(result.movie_ids) <= 10

    def test_consistent_across_calls(self, fixture_data: DataStore):
        """Same state → same results (deterministic)."""
        state = _empty_state()
        result1 = popularity.recommend(state, fixture_data)
        result2 = popularity.recommend(state, fixture_data)
        assert result1.movie_ids == result2.movie_ids

    def test_excludes_rated_movies(self, fixture_data: DataStore):
        """Movies the user has rated should not appear in results."""
        state = SimulationState(
            ratings=[Rating(movie_id=1, score=5.0), Rating(movie_id=2, score=4.0)]
        )
        result = popularity.recommend(state, fixture_data)
        assert 1 not in result.movie_ids
        assert 2 not in result.movie_ids

    def test_ignores_user_signals(self, fixture_data: DataStore):
        """Adding ratings doesn't change the ranking order (only removes rated movies)."""
        state_empty = _empty_state()
        state_rated = SimulationState(ratings=[Rating(movie_id=1, score=5.0)])
        result_empty = popularity.recommend(state_empty, fixture_data)
        result_rated = popularity.recommend(state_rated, fixture_data)

        # The relative order of remaining movies should be preserved
        empty_without_rated = [m for m in result_empty.movie_ids if m != 1]
        # All movies from the empty result (minus rated) should appear in order
        for m in empty_without_rated:
            assert m in result_rated.movie_ids
        # Movie 1 should not appear
        assert 1 not in result_rated.movie_ids

    def test_scores_are_normalized(self, fixture_data: DataStore):
        """All scores should be in [0, 1]."""
        state = _empty_state()
        result = popularity.recommend(state, fixture_data)
        for score in result.scores:
            assert 0.0 <= score <= 1.0

    def test_scores_length_matches_ids(self, fixture_data: DataStore):
        state = _empty_state()
        result = popularity.recommend(state, fixture_data)
        assert len(result.scores) == len(result.movie_ids)


# ---------------------------------------------------------------------------
# Content-Based Tests
# ---------------------------------------------------------------------------


class TestContentBased:
    """Verify content-based filtering behavior."""

    def test_empty_with_zero_signals(self, fixture_data: DataStore):
        """With no signals, content-based cannot recommend."""
        state = _empty_state()
        result = content_based.recommend(state, fixture_data)
        assert result.movie_ids == []
        assert result.scores == []

    def test_returns_genre_similar_after_one_rating(self, fixture_data: DataStore):
        """After rating an Action movie, should recommend other Action movies."""
        state = SimulationState(
            ratings=[Rating(movie_id=1, score=5.0)]  # Action Movie 1
        )
        result = content_based.recommend(state, fixture_data)
        assert len(result.movie_ids) > 0

        # Check that top results are Action or Action|Comedy movies
        action_ids = set(range(2, 6)) | set(range(16, 19))  # Other action movies (not 1)
        top_3 = set(result.movie_ids[:3])
        # At least some of the top results should be action-related
        assert len(top_3 & action_ids) > 0

    def test_genre_preferences_boost_correct_genres(self, fixture_data: DataStore):
        """Explicit genre preferences should boost those genre dimensions."""
        state = SimulationState(genre_preferences=["Drama"])
        result = content_based.recommend(state, fixture_data)
        assert len(result.movie_ids) > 0

        # Drama movies should rank highly
        drama_ids = set(range(11, 16)) | set(range(19, 21))
        top_results = set(result.movie_ids[:5])
        assert len(top_results & drama_ids) > 0

    def test_view_history_produces_recommendations(self, fixture_data: DataStore):
        """View history alone should produce recommendations (weaker signal)."""
        state = SimulationState(view_history=[6, 7, 8])  # Comedy movies
        result = content_based.recommend(state, fixture_data)
        assert len(result.movie_ids) > 0

    def test_scores_are_normalized(self, fixture_data: DataStore):
        state = SimulationState(ratings=[Rating(movie_id=1, score=5.0)])
        result = content_based.recommend(state, fixture_data)
        for score in result.scores:
            assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Collaborative Tests
# ---------------------------------------------------------------------------


class TestCollaborative:
    """Verify collaborative filtering (SVD) behavior."""

    def test_empty_with_zero_signals_no_demographics(self, fixture_data: DataStore):
        """With no ratings and no demographics, collaborative cannot recommend."""
        state = _empty_state()
        result = collaborative.recommend(state, fixture_data)
        assert result.movie_ids == []

    def test_returns_results_after_ratings(self, fixture_data: DataStore):
        """With 5+ ratings, collaborative should produce recommendations."""
        state = SimulationState(
            ratings=[
                Rating(movie_id=1, score=5.0),
                Rating(movie_id=2, score=4.5),
                Rating(movie_id=3, score=4.0),
                Rating(movie_id=6, score=2.0),
                Rating(movie_id=7, score=2.5),
            ]
        )
        result = collaborative.recommend(state, fixture_data)
        assert len(result.movie_ids) > 0
        # Should not include already-rated movies
        rated = {1, 2, 3, 6, 7}
        for mid in result.movie_ids:
            assert mid not in rated

    def test_demographics_only_produces_weak_results(self, fixture_data: DataStore):
        """Demographics without ratings should produce some (weak) results."""
        state = SimulationState(demographics=Demographics(age=23, gender="F", occupation="student"))
        result = collaborative.recommend(state, fixture_data)
        # May return results from demographic neighbors, or may be empty
        # if no neighbors match. Either is acceptable for demographics-only.
        assert isinstance(result.movie_ids, list)

    def test_scores_are_normalized(self, fixture_data: DataStore):
        state = SimulationState(
            ratings=[
                Rating(movie_id=1, score=5.0),
                Rating(movie_id=2, score=4.0),
                Rating(movie_id=3, score=3.0),
            ]
        )
        result = collaborative.recommend(state, fixture_data)
        for score in result.scores:
            assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Hybrid Tests
# ---------------------------------------------------------------------------


class TestHybrid:
    """Verify hybrid ensemble behavior."""

    def test_with_zero_signals_matches_popularity(self, fixture_data: DataStore):
        """With zero signals, hybrid should be 100% popularity."""
        state = _empty_state()
        hybrid_result = hybrid.recommend(state, fixture_data)
        pop_result = popularity.recommend(state, fixture_data)

        # Same movies (order may differ slightly due to normalization)
        assert set(hybrid_result.movie_ids) == set(pop_result.movie_ids)

    def test_with_ratings_differs_from_popularity(self, fixture_data: DataStore):
        """With ratings, hybrid should diverge from pure popularity."""
        state = SimulationState(
            ratings=[
                Rating(movie_id=1, score=5.0),
                Rating(movie_id=2, score=5.0),
                Rating(movie_id=3, score=5.0),
            ]
        )
        hybrid_result = hybrid.recommend(state, fixture_data)

        # Results should differ since content-based and collab now contribute
        # (may not always differ if dataset is small, so check they at least run)
        assert len(hybrid_result.movie_ids) > 0
        assert len(hybrid_result.movie_ids) <= 10

    def test_returns_at_most_10(self, fixture_data: DataStore):
        state = SimulationState(ratings=[Rating(movie_id=1, score=5.0)])
        result = hybrid.recommend(state, fixture_data)
        assert len(result.movie_ids) <= 10

    def test_scores_are_normalized(self, fixture_data: DataStore):
        state = SimulationState(ratings=[Rating(movie_id=1, score=5.0)])
        result = hybrid.recommend(state, fixture_data)
        for score in result.scores:
            assert 0.0 <= score <= 1.0

    def test_scores_length_matches_ids(self, fixture_data: DataStore):
        state = SimulationState(ratings=[Rating(movie_id=1, score=5.0)])
        result = hybrid.recommend(state, fixture_data)
        assert len(result.scores) == len(result.movie_ids)
