"""Hybrid ensemble recommender.

Combines popularity, content-based, and collaborative filtering using
adaptive weights that shift based on the available signals. This mirrors
how production recommendation systems handle the cold-start problem:
rely on non-personalized methods initially, then transition to
personalized methods as user data accumulates.

Weight scheme (from spec Section 7.1):
  - Zero signals:           100% popularity
  - Ratings only:           40% content + 40% collab + 20% popularity
  - Ratings + demographics: 30% content + 50% collab + 20% popularity
  - All signals:            25% content + 50% collab + 15% popularity + 10% genre boost
"""

from app.data.loader import DataStore
from app.models.simulation import SimulationState
from app.services.algorithms import collaborative, content_based, popularity
from app.services.algorithms.base import RecommenderResult

TOP_K = 10


def _determine_weights(
    state: SimulationState,
) -> tuple[float, float, float]:
    """Determine algorithm weights based on available signals.

    Returns:
        Tuple of (popularity_weight, content_weight, collab_weight).
    """
    has_ratings = len(state.ratings) > 0
    has_demographics = (
        state.demographics.age is not None
        or state.demographics.gender is not None
        or state.demographics.occupation is not None
    )
    has_genre_prefs = len(state.genre_preferences) > 0
    has_view_history = len(state.view_history) > 0
    has_all = has_ratings and has_demographics and (has_genre_prefs or has_view_history)

    if not has_ratings and not has_demographics and not has_genre_prefs and not has_view_history:
        # Zero signals → 100% popularity
        return (1.0, 0.0, 0.0)
    elif has_all:
        # All signals → 15% popularity, 25% content, 50% collab
        # (the 10% genre boost is already baked into content-based via genre_preferences)
        return (0.15, 0.25, 0.50)
    elif has_ratings and has_demographics:
        # Ratings + demographics → 20% popularity, 30% content, 50% collab
        return (0.20, 0.30, 0.50)
    elif has_ratings:
        # Ratings only → 20% popularity, 40% content, 40% collab
        return (0.20, 0.40, 0.40)
    else:
        # Demographics only or genre prefs only — limited personalization
        # Content-based can use genre prefs, collab can use demographics
        return (0.60, 0.20, 0.20)


def _normalize_scores(result: RecommenderResult) -> dict[int, float]:
    """Min-max normalize scores to [0, 1] and return as movie_id → score dict."""
    if not result.movie_ids:
        return {}

    scores = result.scores
    min_s = min(scores)
    max_s = max(scores)
    score_range = max_s - min_s

    normalized: dict[int, float] = {}
    for mid, s in zip(result.movie_ids, result.scores):
        if score_range > 0:
            normalized[mid] = (s - min_s) / score_range
        else:
            normalized[mid] = 1.0

    return normalized


def recommend(state: SimulationState, data: DataStore) -> RecommenderResult:
    """Combine all three algorithms with adaptive weights."""
    pop_weight, content_weight, collab_weight = _determine_weights(state)

    # Run each algorithm
    pop_result = popularity.recommend(state, data)
    content_result = content_based.recommend(state, data)
    collab_result = collaborative.recommend(state, data)

    # Normalize each algorithm's scores
    pop_scores = _normalize_scores(pop_result)
    content_scores = _normalize_scores(content_result)
    collab_scores = _normalize_scores(collab_result)

    # Collect all candidate movie IDs
    all_candidates: set[int] = set()
    all_candidates.update(pop_scores.keys())
    all_candidates.update(content_scores.keys())
    all_candidates.update(collab_scores.keys())

    # Compute combined score for each candidate
    combined: dict[int, float] = {}
    for mid in all_candidates:
        score = 0.0
        score += pop_weight * pop_scores.get(mid, 0.0)
        score += content_weight * content_scores.get(mid, 0.0)
        score += collab_weight * collab_scores.get(mid, 0.0)
        combined[mid] = score

    # Sort by combined score descending, take top-k
    ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:TOP_K]

    if not ranked:
        return RecommenderResult(movie_ids=[], scores=[])

    movie_ids = [r[0] for r in ranked]
    scores = [r[1] for r in ranked]

    # Final normalization to [0, 1]
    max_score = max(scores)
    min_score = min(scores)
    score_range = max_score - min_score
    if score_range > 0:
        scores = [(s - min_score) / score_range for s in scores]
    else:
        scores = [1.0] * len(scores)

    return RecommenderResult(movie_ids=movie_ids, scores=scores)
