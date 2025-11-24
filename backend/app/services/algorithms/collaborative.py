"""Collaborative filtering recommender using SVD.

Wraps scikit-surprise's SVD implementation. On each call, injects the
simulated user's ratings into the MovieLens rating matrix as user_id=0,
trains SVD, and predicts ratings for all unseen movies.

Signals used:
  - Ratings: injected into the rating matrix for SVD training
  - Demographics: used to find similar users for cold-start initialization
  - Genre preferences: NOT used (SVD operates on user-item interactions only)
  - View history: NOT used

With zero ratings and no demographics, returns an empty result.
With zero ratings but demographics set, uses demographic neighbors' average
ratings as a weak signal.
"""

import pandas as pd
import structlog
from surprise import SVD, Dataset, Reader

from app.data.loader import DataStore
from app.models.simulation import SimulationState
from app.services.algorithms.base import RecommenderResult

logger = structlog.get_logger()

# SVD hyperparameters — tuned for interactive demo latency (<1s)
N_FACTORS = 50
N_EPOCHS = 10
SIMULATED_USER_ID = 0

# Demographic neighbor settings
MAX_DEMOGRAPHIC_NEIGHBORS = 10
AGE_TOLERANCE = 5

TOP_K = 10


def _find_demographic_neighbors(state: SimulationState, data: DataStore) -> list[int]:
    """Find users with similar demographics to the simulated user.

    Matches on: age (±5 years), gender (exact), occupation (exact).
    Returns up to MAX_DEMOGRAPHIC_NEIGHBORS user IDs.
    """
    demos = state.demographics
    if demos.age is None and demos.gender is None and demos.occupation is None:
        return []

    users_df = data.users_df
    mask = pd.Series(True, index=users_df.index)

    if demos.age is not None:
        mask &= (users_df["age"] >= demos.age - AGE_TOLERANCE) & (
            users_df["age"] <= demos.age + AGE_TOLERANCE
        )
    if demos.gender is not None:
        mask &= users_df["gender"] == demos.gender
    if demos.occupation is not None:
        mask &= users_df["occupation"] == demos.occupation

    neighbors = users_df[mask]["user_id"].tolist()
    return neighbors[:MAX_DEMOGRAPHIC_NEIGHBORS]


def _get_neighbor_ratings(neighbor_ids: list[int], data: DataStore) -> list[tuple[int, float]]:
    """Get average ratings from demographic neighbors for cold-start.

    Returns a list of (movie_id, avg_rating) tuples, using only movies
    rated by at least 2 neighbors to reduce noise.
    """
    if not neighbor_ids:
        return []

    ratings_df = data.ratings_df
    neighbor_ratings = ratings_df[ratings_df["user_id"].isin(neighbor_ids)]

    # Average rating per movie, require at least 2 raters for stability
    movie_avgs = neighbor_ratings.groupby("movie_id")["rating"].agg(["mean", "count"])
    stable = movie_avgs[movie_avgs["count"] >= 2]

    return [(int(mid), float(avg)) for mid, avg in stable["mean"].items()]


def recommend(state: SimulationState, data: DataStore) -> RecommenderResult:
    """Recommend movies using SVD collaborative filtering."""
    has_ratings = len(state.ratings) > 0
    has_demographics = (
        state.demographics.age is not None
        or state.demographics.gender is not None
        or state.demographics.occupation is not None
    )

    # With zero signals, can't place user in latent space
    if not has_ratings and not has_demographics:
        return RecommenderResult(movie_ids=[], scores=[])

    # Build the ratings to inject for the simulated user
    sim_user_ratings: list[tuple[int, int, float]] = []

    # Add explicit ratings from the simulated user
    for r in state.ratings:
        sim_user_ratings.append((SIMULATED_USER_ID, r.movie_id, r.score))

    # If demographics but few/no ratings, add neighbor averages as weak signal
    if has_demographics and len(state.ratings) < 5:
        neighbor_ids = _find_demographic_neighbors(state, data)
        if neighbor_ids:
            neighbor_avg_ratings = _get_neighbor_ratings(neighbor_ids, data)
            # Only add neighbor ratings for movies the user hasn't explicitly rated
            rated_movie_ids = {r.movie_id for r in state.ratings}
            for movie_id, avg_rating in neighbor_avg_ratings:
                if movie_id not in rated_movie_ids:
                    sim_user_ratings.append((SIMULATED_USER_ID, movie_id, avg_rating))

    if not sim_user_ratings:
        return RecommenderResult(movie_ids=[], scores=[])

    # Build combined ratings DataFrame
    existing_ratings = data.ratings_df[["user_id", "movie_id", "rating"]].copy()

    new_rows = pd.DataFrame(sim_user_ratings, columns=["user_id", "movie_id", "rating"])
    combined = pd.concat([existing_ratings, new_rows], ignore_index=True)

    # Train SVD
    reader = Reader(rating_scale=(1.0, 5.0))
    surprise_data = Dataset.load_from_df(combined, reader)
    trainset = surprise_data.build_full_trainset()

    algo = SVD(n_factors=N_FACTORS, n_epochs=N_EPOCHS, verbose=False)
    algo.fit(trainset)

    # Predict ratings for all unseen movies
    rated_ids = {r.movie_id for r in state.ratings}
    all_movie_ids = data.movies_df["movie_id"].tolist()

    predictions: list[tuple[int, float]] = []
    for movie_id in all_movie_ids:
        if movie_id not in rated_ids:
            pred = algo.predict(SIMULATED_USER_ID, movie_id)
            predictions.append((movie_id, pred.est))

    # Sort by predicted rating descending, take top-k
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_predictions = predictions[:TOP_K]

    movie_ids = [p[0] for p in top_predictions]
    scores = [p[1] for p in top_predictions]

    # Normalize scores to [0, 1]
    if scores:
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score
        if score_range > 0:
            scores = [(s - min_score) / score_range for s in scores]
        else:
            scores = [1.0] * len(scores)

    return RecommenderResult(movie_ids=movie_ids, scores=scores)
