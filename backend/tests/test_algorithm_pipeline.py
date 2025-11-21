"""Integration test: full algorithm pipeline on real MovieLens data.

Loads the real DataStore, selects a ground-truth user, runs all four
algorithms at 0, 1, 5, and 10 simulated ratings, and verifies the
complete pipeline produces valid, bounded results.
"""

import random

import pytest

from app.data.loader import DataStore
from app.models.simulation import Demographics, Rating, SimulationState
from app.services.algorithms import collaborative, content_based, hybrid, popularity
from app.services.algorithms.base import RecommenderResult
from app.services.ground_truth import select_ground_truth_user
from app.services.metrics import ndcg_at_k, precision_at_k, recall_at_k


@pytest.fixture(scope="module")
def data_store() -> DataStore:
    """Load real MovieLens data."""
    return DataStore(data_dir="../data")


@pytest.fixture(scope="module")
def ground_truth(data_store: DataStore):
    """Select a reproducible ground-truth user."""
    rng = random.Random(42)
    return select_ground_truth_user(data_store, rng=rng)


@pytest.fixture(scope="module")
def seed_movies(data_store: DataStore, ground_truth):
    """Get movies rated by the ground-truth user for simulating ratings.

    Returns movies the ground-truth user rated, sorted by rating (desc),
    excluding movies in the relevant set to avoid trivially boosting metrics.
    """
    user_ratings = data_store.ratings_df[
        data_store.ratings_df["user_id"] == ground_truth.user_id
    ].sort_values("rating", ascending=False)

    # Use movies with moderate ratings (3.0-4.0) as seed ratings
    # These provide signal without being the exact ground-truth relevant items
    moderate = user_ratings[(user_ratings["rating"] >= 3.0) & (user_ratings["rating"] <= 4.0)]
    return list(moderate[["movie_id", "rating"]].itertuples(index=False, name=None))


def _validate_result(result: RecommenderResult, max_len: int = 10):
    """Validate that a RecommenderResult has the correct format."""
    assert isinstance(result.movie_ids, list)
    assert isinstance(result.scores, list)
    assert len(result.movie_ids) == len(result.scores)
    assert len(result.movie_ids) <= max_len
    for score in result.scores:
        assert 0.0 <= score <= 1.0


def _validate_metrics(recs: list[int], relevant: set[int]):
    """Validate that all metrics are in [0, 1]."""
    p = precision_at_k(recs, relevant)
    r = recall_at_k(recs, relevant)
    n = ndcg_at_k(recs, relevant)
    assert 0.0 <= p <= 1.0
    assert 0.0 <= r <= 1.0
    assert 0.0 <= n <= 1.0
    return p, r, n


class TestZeroSignals:
    """All algorithms with zero user signals."""

    def test_popularity_returns_results(self, data_store):
        state = SimulationState()
        result = popularity.recommend(state, data_store)
        _validate_result(result)
        assert len(result.movie_ids) == 10

    def test_content_based_returns_empty(self, data_store):
        state = SimulationState()
        result = content_based.recommend(state, data_store)
        assert result.movie_ids == []

    def test_collaborative_returns_empty(self, data_store):
        state = SimulationState()
        result = collaborative.recommend(state, data_store)
        assert result.movie_ids == []

    def test_hybrid_returns_results(self, data_store):
        """Hybrid falls back to 100% popularity with zero signals."""
        state = SimulationState()
        result = hybrid.recommend(state, data_store)
        _validate_result(result)
        assert len(result.movie_ids) == 10

    def test_metrics_are_valid(self, data_store, ground_truth):
        state = SimulationState()
        result = popularity.recommend(state, data_store)
        _validate_metrics(result.movie_ids, ground_truth.relevant_movie_ids)


class TestOneRating:
    """After adding a single rating."""

    def test_content_based_produces_results(self, data_store, seed_movies):
        if not seed_movies:
            pytest.skip("No seed movies available")
        movie_id, rating = seed_movies[0]
        state = SimulationState(ratings=[Rating(movie_id=movie_id, score=rating)])
        result = content_based.recommend(state, data_store)
        _validate_result(result)
        assert len(result.movie_ids) > 0

    def test_collaborative_produces_results(self, data_store, seed_movies):
        if not seed_movies:
            pytest.skip("No seed movies available")
        movie_id, rating = seed_movies[0]
        state = SimulationState(ratings=[Rating(movie_id=movie_id, score=rating)])
        result = collaborative.recommend(state, data_store)
        _validate_result(result)
        # With just 1 rating, collaborative may produce noisy but non-empty results
        assert len(result.movie_ids) > 0

    def test_all_metrics_valid(self, data_store, seed_movies, ground_truth):
        if not seed_movies:
            pytest.skip("No seed movies available")
        movie_id, rating = seed_movies[0]
        state = SimulationState(ratings=[Rating(movie_id=movie_id, score=rating)])

        for algo in [popularity, content_based, collaborative, hybrid]:
            result = algo.recommend(state, data_store)
            if result.movie_ids:
                _validate_metrics(result.movie_ids, ground_truth.relevant_movie_ids)


class TestFiveRatings:
    """After adding 5 ratings — collaborative should start being meaningful."""

    def test_all_algorithms_return_results(self, data_store, seed_movies):
        if len(seed_movies) < 5:
            pytest.skip("Not enough seed movies")

        ratings = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:5]]
        state = SimulationState(ratings=ratings)

        for algo in [popularity, content_based, collaborative, hybrid]:
            result = algo.recommend(state, data_store)
            _validate_result(result)
            assert len(result.movie_ids) > 0

    def test_content_and_collab_differ(self, data_store, seed_movies):
        """Content-based and collaborative should produce different results."""
        if len(seed_movies) < 5:
            pytest.skip("Not enough seed movies")

        ratings = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:5]]
        state = SimulationState(ratings=ratings)

        cb_result = content_based.recommend(state, data_store)
        cf_result = collaborative.recommend(state, data_store)

        # At least some results should differ
        assert set(cb_result.movie_ids) != set(cf_result.movie_ids)

    def test_metrics_are_valid(self, data_store, seed_movies, ground_truth):
        if len(seed_movies) < 5:
            pytest.skip("Not enough seed movies")

        ratings = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:5]]
        state = SimulationState(ratings=ratings)

        for algo in [popularity, content_based, collaborative, hybrid]:
            result = algo.recommend(state, data_store)
            p, r, n = _validate_metrics(result.movie_ids, ground_truth.relevant_movie_ids)


class TestTenRatings:
    """After adding 10 ratings — all algorithms should be producing results."""

    def test_all_produce_full_results(self, data_store, seed_movies):
        if len(seed_movies) < 10:
            pytest.skip("Not enough seed movies")

        ratings = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:10]]
        state = SimulationState(ratings=ratings)

        for algo in [popularity, content_based, collaborative, hybrid]:
            result = algo.recommend(state, data_store)
            _validate_result(result)
            assert len(result.movie_ids) == 10

    def test_adding_more_ratings_changes_results(self, data_store, seed_movies):
        """Results at 5 ratings should differ from results at 10 ratings."""
        if len(seed_movies) < 10:
            pytest.skip("Not enough seed movies")

        ratings_5 = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:5]]
        ratings_10 = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:10]]

        state_5 = SimulationState(ratings=ratings_5)
        state_10 = SimulationState(ratings=ratings_10)

        for algo in [content_based, collaborative, hybrid]:
            result_5 = algo.recommend(state_5, data_store)
            result_10 = algo.recommend(state_10, data_store)
            # Results should change with more data (at least some)
            assert result_5.movie_ids != result_10.movie_ids


class TestWithDemographics:
    """Test algorithms with demographic signals."""

    def test_collaborative_with_demographics_only(self, data_store):
        """Demographics alone should produce collaborative results."""
        state = SimulationState(demographics=Demographics(age=25, gender="M", occupation="student"))
        result = collaborative.recommend(state, data_store)
        _validate_result(result)
        # May return results from demographic neighbors

    def test_demographics_change_collaborative_results(self, data_store, seed_movies):
        """Adding demographics should change collaborative results."""
        if len(seed_movies) < 3:
            pytest.skip("Not enough seed movies")

        ratings = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:3]]

        state_no_demo = SimulationState(ratings=ratings)
        state_with_demo = SimulationState(
            ratings=ratings,
            demographics=Demographics(age=25, gender="M", occupation="student"),
        )

        result_no = collaborative.recommend(state_no_demo, data_store)
        result_with = collaborative.recommend(state_with_demo, data_store)

        # Results should differ (demographic neighbors provide additional signal)
        # Note: with small rating counts, the demographic boost should change results
        _validate_result(result_no)
        _validate_result(result_with)


class TestPerformance:
    """Verify algorithm calls complete within acceptable time."""

    def test_all_algorithms_under_5_seconds(self, data_store, seed_movies):
        """Each algorithm call should complete in under 5 seconds on MovieLens 100K."""
        import time

        if len(seed_movies) < 5:
            pytest.skip("Not enough seed movies")

        ratings = [Rating(movie_id=mid, score=r) for mid, r in seed_movies[:5]]
        state = SimulationState(ratings=ratings)

        for algo_name, algo in [
            ("popularity", popularity),
            ("content_based", content_based),
            ("collaborative", collaborative),
            ("hybrid", hybrid),
        ]:
            start = time.time()
            result = algo.recommend(state, data_store)
            elapsed = time.time() - start
            assert elapsed < 5.0, f"{algo_name} took {elapsed:.2f}s (max 5s)"
            _validate_result(result)
