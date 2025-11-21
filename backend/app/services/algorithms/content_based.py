"""Content-based filtering recommender.

Builds a user taste vector from rated movies' genre profiles and recommends
unseen movies whose genre profile is most similar (cosine similarity).

Signals used:
  - Ratings: genre vectors weighted by rating score
  - Genre preferences: direct boost to those genre dimensions
  - View history: genre vectors with a weaker weight (0.5)
  - Demographics: NOT used (content-based operates on item features only)

With zero signals, returns an empty result (cannot recommend without
knowing any preferences).
"""

import numpy as np
from numpy.typing import NDArray

from app.data.loader import DataStore
from app.models.simulation import SimulationState
from app.services.algorithms.base import RecommenderResult

TOP_K = 10
VIEW_HISTORY_WEIGHT = 0.5

# Module-level cache for genre vectors
_cached_genre_matrix: NDArray[np.float64] | None = None
_cached_genre_labels: list[str] | None = None
_cached_movie_ids: list[int] | None = None
_cached_data_id: int | None = None


def _build_genre_matrix(data: DataStore) -> tuple[NDArray[np.float64], list[str], list[int]]:
    """Build a (num_movies x num_genres) binary matrix from movie genre strings.

    Returns:
        genre_matrix: Binary matrix where entry [i, j] = 1 if movie i has genre j.
        genre_labels: Ordered list of genre names (columns of the matrix).
        movie_ids: Ordered list of movie IDs (rows of the matrix).
    """
    movies_df = data.movies_df

    # Extract all unique genres across the dataset
    all_genres: set[str] = set()
    for genres_str in movies_df["genres"]:
        if genres_str and isinstance(genres_str, str):
            all_genres.update(genres_str.split("|"))
    genre_labels = sorted(all_genres)
    genre_to_idx = {g: i for i, g in enumerate(genre_labels)}

    # Build the binary matrix
    movie_ids = movies_df["movie_id"].tolist()
    genre_matrix = np.zeros((len(movie_ids), len(genre_labels)), dtype=np.float64)

    for row_idx, genres_str in enumerate(movies_df["genres"]):
        if genres_str and isinstance(genres_str, str):
            for genre in genres_str.split("|"):
                if genre in genre_to_idx:
                    genre_matrix[row_idx, genre_to_idx[genre]] = 1.0

    return genre_matrix, genre_labels, movie_ids


def _get_genre_data(
    data: DataStore,
) -> tuple[NDArray[np.float64], list[str], list[int]]:
    """Get cached genre matrix, labels, and movie IDs."""
    global _cached_genre_matrix, _cached_genre_labels, _cached_movie_ids, _cached_data_id

    data_id = id(data)
    if _cached_genre_matrix is None or _cached_data_id != data_id:
        _cached_genre_matrix, _cached_genre_labels, _cached_movie_ids = _build_genre_matrix(data)
        _cached_data_id = data_id

    return _cached_genre_matrix, _cached_genre_labels, _cached_movie_ids


def _cosine_similarity(
    vec: NDArray[np.float64], matrix: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Compute cosine similarity between a vector and each row of a matrix."""
    vec_norm = np.linalg.norm(vec)
    if vec_norm == 0:
        return np.zeros(matrix.shape[0])

    row_norms = np.linalg.norm(matrix, axis=1)
    # Avoid division by zero for movies with no genres
    row_norms = np.where(row_norms == 0, 1.0, row_norms)

    return (matrix @ vec) / (row_norms * vec_norm)


def recommend(state: SimulationState, data: DataStore) -> RecommenderResult:
    """Recommend movies by genre similarity to the user's taste profile."""
    # With zero signals, cannot compute a taste vector
    has_ratings = len(state.ratings) > 0
    has_genre_prefs = len(state.genre_preferences) > 0
    has_view_history = len(state.view_history) > 0

    if not has_ratings and not has_genre_prefs and not has_view_history:
        return RecommenderResult(movie_ids=[], scores=[])

    genre_matrix, genre_labels, movie_ids = _get_genre_data(data)
    genre_to_idx = {g: i for i, g in enumerate(genre_labels)}
    movie_id_to_row = {mid: i for i, mid in enumerate(movie_ids)}

    # Build user taste vector
    taste_vector = np.zeros(len(genre_labels), dtype=np.float64)

    # 1) Ratings: add genre vectors weighted by rating score
    for rating in state.ratings:
        row_idx = movie_id_to_row.get(rating.movie_id)
        if row_idx is not None:
            taste_vector += genre_matrix[row_idx] * rating.score

    # 2) Genre preferences: direct boost to those dimensions
    for genre_name in state.genre_preferences:
        idx = genre_to_idx.get(genre_name)
        if idx is not None:
            taste_vector[idx] += 5.0  # Strong boost (equivalent to a top rating)

    # 3) View history: add genre vectors with reduced weight
    for movie_id in state.view_history:
        row_idx = movie_id_to_row.get(movie_id)
        if row_idx is not None:
            taste_vector += genre_matrix[row_idx] * VIEW_HISTORY_WEIGHT

    # Compute cosine similarity against all movies
    similarities = _cosine_similarity(taste_vector, genre_matrix)

    # Build exclusion set: already rated + already in view history
    exclude_ids = {r.movie_id for r in state.ratings}

    # Rank by similarity, filter exclusions, take top-k
    ranked_indices = np.argsort(similarities)[::-1]

    result_ids: list[int] = []
    result_scores: list[float] = []
    for idx in ranked_indices:
        mid = movie_ids[idx]
        if mid not in exclude_ids and similarities[idx] > 0:
            result_ids.append(mid)
            result_scores.append(float(similarities[idx]))
        if len(result_ids) >= TOP_K:
            break

    # Normalize scores to [0, 1]
    if result_scores:
        max_score = max(result_scores)
        min_score = min(result_scores)
        score_range = max_score - min_score
        if score_range > 0:
            result_scores = [(s - min_score) / score_range for s in result_scores]
        else:
            result_scores = [1.0] * len(result_scores)

    return RecommenderResult(movie_ids=result_ids, scores=result_scores)
