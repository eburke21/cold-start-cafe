"""Popularity baseline recommender.

Ranks all movies by Bayesian average rating (global, user-agnostic).
This algorithm ignores all user signals — it always returns the same
top movies, minus any the user has already rated.

Formula: score = (avg_rating * num_ratings) / (num_ratings + damping_factor)
Damping factor = 25, which ensures movies with very few ratings are
pulled toward zero (prevents one 5-star rating from topping the list).
"""

from app.data.loader import DataStore
from app.models.simulation import SimulationState
from app.services.algorithms.base import RecommenderResult

# Damping factor for Bayesian average (higher = more conservative)
DAMPING_FACTOR = 25

# Number of recommendations to return
TOP_K = 10

# Module-level cache: computed once per DataStore, reused across calls
_cached_rankings: list[tuple[int, float]] | None = None
_cached_data_id: int | None = None


def _compute_rankings(data: DataStore) -> list[tuple[int, float]]:
    """Compute Bayesian average scores for all movies, sorted descending."""
    ratings_df = data.ratings_df

    # Group by movie: compute mean rating and count
    movie_stats = ratings_df.groupby("movie_id")["rating"].agg(["mean", "count"])

    # Bayesian average
    movie_stats["score"] = (movie_stats["mean"] * movie_stats["count"]) / (
        movie_stats["count"] + DAMPING_FACTOR
    )

    # Sort by score descending, return as list of (movie_id, score)
    ranked = movie_stats.sort_values("score", ascending=False)
    return [(int(movie_id), float(score)) for movie_id, score in ranked["score"].items()]


def recommend(state: SimulationState, data: DataStore) -> RecommenderResult:
    """Return top-k movies by popularity, excluding already-rated movies."""
    global _cached_rankings, _cached_data_id

    # Cache rankings per DataStore instance (id changes if reloaded)
    data_id = id(data)
    if _cached_rankings is None or _cached_data_id != data_id:
        _cached_rankings = _compute_rankings(data)
        _cached_data_id = data_id

    # Collect movie IDs the simulated user has already rated
    rated_ids = {r.movie_id for r in state.ratings}

    # Filter out rated movies, take top-k
    movie_ids: list[int] = []
    scores: list[float] = []
    for movie_id, score in _cached_rankings:
        if movie_id not in rated_ids:
            movie_ids.append(movie_id)
            scores.append(score)
        if len(movie_ids) >= TOP_K:
            break

    # Normalize scores to [0, 1]
    if scores:
        max_score = scores[0]  # Already sorted descending
        min_score = scores[-1]
        score_range = max_score - min_score
        if score_range > 0:
            scores = [(s - min_score) / score_range for s in scores]
        else:
            scores = [1.0] * len(scores)

    return RecommenderResult(movie_ids=movie_ids, scores=scores)
