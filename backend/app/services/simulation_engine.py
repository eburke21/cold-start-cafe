"""Central orchestrator for simulation signal processing.

Takes a SimulationState and a new signal, runs all four algorithms,
computes metrics against ground truth, resolves movie metadata,
and returns a complete SimulationStep.
"""

import time

import structlog

from app.data.loader import DataStore
from app.models.enums import AlgorithmName, SignalType
from app.models.simulation import (
    AddSignalRequest,
    AlgorithmResult,
    MovieRecommendation,
    Rating,
    Signal,
    SimulationState,
    SimulationStep,
)
from app.services.algorithms import collaborative, content_based, hybrid, popularity
from app.services.algorithms.base import RecommenderResult
from app.services.ground_truth import GroundTruthUser
from app.services.metrics import ndcg_at_k, precision_at_k, recall_at_k

logger = structlog.get_logger()


def _resolve_recommendations(
    result: RecommenderResult, data: DataStore
) -> list[MovieRecommendation]:
    """Convert algorithm output (movie IDs + scores) into full MovieRecommendation objects."""
    recommendations = []
    for movie_id, score in zip(result.movie_ids, result.scores):
        movie = data.get_movie(movie_id)
        if movie:
            recommendations.append(
                MovieRecommendation(
                    movie_id=movie_id,
                    title=movie["title"],
                    genres=movie.get("genres", ""),
                    score=score,
                )
            )
    return recommendations


def _run_algorithm(
    name: AlgorithmName,
    recommend_fn,
    state: SimulationState,
    data: DataStore,
    ground_truth: GroundTruthUser,
) -> AlgorithmResult:
    """Run a single algorithm and compute its metrics."""
    result = recommend_fn(state, data)
    recommendations = _resolve_recommendations(result, data)

    return AlgorithmResult(
        algorithm=name,
        recommendations=recommendations,
        precision_at_10=precision_at_k(result.movie_ids, ground_truth.relevant_movie_ids),
        recall_at_10=recall_at_k(result.movie_ids, ground_truth.relevant_movie_ids),
        ndcg_at_10=ndcg_at_k(result.movie_ids, ground_truth.relevant_movie_ids),
    )


def _generate_placeholder_narration(step_number: int, signal: Signal | None) -> str:
    """Generate a placeholder narration string for a simulation step.

    Real LLM narration comes in Phase 5. For now, describe what happened.
    """
    if step_number == 0:
        return (
            "Welcome to the cold-start problem! You've just walked into the café as a "
            "complete stranger. The algorithms have nothing to work with — only the "
            "popularity baseline can make recommendations. Try adding some signals to "
            "help the algorithms learn your taste."
        )

    signal_descriptions = {
        SignalType.RATING: "You rated a movie! Content-based and collaborative filtering now have "
        "a data point to work with.",
        SignalType.DEMOGRAPHIC: "Demographics added! Collaborative filtering can now find similar "
        "users based on age, gender, and occupation.",
        SignalType.GENRE_PREFERENCE: "Genre preferences set! Content-based filtering gets a direct "
        "boost for these genres.",
        SignalType.VIEW_HISTORY: "Viewing history added! Content-based filtering treats these as "
        "weak positive signals for the genres you've browsed.",
    }

    if signal:
        return signal_descriptions.get(
            signal.type,
            f"Signal added at step {step_number}.",
        )
    return f"Step {step_number} processed."


def apply_signal(state: SimulationState, signal_request: AddSignalRequest) -> Signal:
    """Validate and apply a signal to the simulation state.

    Mutates the state in place and returns the Signal record.

    Raises:
        ValueError: If the signal payload is invalid.
    """
    step_number = len(state.steps)
    signal = Signal(type=signal_request.type, step=step_number, payload=signal_request.payload)

    if signal_request.type == SignalType.RATING:
        movie_id = signal_request.payload.get("movie_id")
        score = signal_request.payload.get("score")
        if movie_id is None or score is None:
            raise ValueError("Rating signal requires 'movie_id' and 'score' in payload")
        state.ratings.append(Rating(movie_id=int(movie_id), score=float(score)))

    elif signal_request.type == SignalType.DEMOGRAPHIC:
        age = signal_request.payload.get("age")
        gender = signal_request.payload.get("gender")
        occupation = signal_request.payload.get("occupation")
        if age is not None:
            state.demographics.age = int(age)
        if gender is not None:
            state.demographics.gender = str(gender)
        if occupation is not None:
            state.demographics.occupation = str(occupation)

    elif signal_request.type == SignalType.GENRE_PREFERENCE:
        genres = signal_request.payload.get("genres")
        if not genres or not isinstance(genres, list):
            raise ValueError("Genre preference signal requires 'genres' list in payload")
        state.genre_preferences = [str(g) for g in genres]

    elif signal_request.type == SignalType.VIEW_HISTORY:
        movie_ids = signal_request.payload.get("movie_ids")
        if not movie_ids or not isinstance(movie_ids, list):
            raise ValueError("View history signal requires 'movie_ids' list in payload")
        state.view_history.extend(int(mid) for mid in movie_ids)

    else:
        raise ValueError(f"Unknown signal type: {signal_request.type}")

    return signal


def run_step(
    state: SimulationState,
    data: DataStore,
    ground_truth: GroundTruthUser,
    signal: Signal | None = None,
) -> SimulationStep:
    """Run all four algorithms and produce a complete simulation step.

    Args:
        state: Current simulation state (with signals already applied).
        data: The DataStore with MovieLens data.
        ground_truth: The held-out user for metric evaluation.
        signal: The signal that was just added (None for step 0).

    Returns:
        A SimulationStep with all algorithm results and narration.
    """
    step_number = len(state.steps)
    start_time = time.time()

    # Run all four algorithms
    algorithms = [
        (AlgorithmName.POPULARITY, popularity.recommend),
        (AlgorithmName.CONTENT_BASED, content_based.recommend),
        (AlgorithmName.COLLABORATIVE, collaborative.recommend),
        (AlgorithmName.HYBRID, hybrid.recommend),
    ]

    results = []
    for name, recommend_fn in algorithms:
        algo_result = _run_algorithm(name, recommend_fn, state, data, ground_truth)
        results.append(algo_result)

    narration = _generate_placeholder_narration(step_number, signal)

    step = SimulationStep(
        step_number=step_number,
        signal_added=signal,
        results=results,
        narration=narration,
    )

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(
        "Simulation step completed",
        step_number=step_number,
        signal_type=signal.type if signal else None,
        computation_time_ms=round(elapsed_ms, 1),
    )

    return step


def get_genre_distribution(data: DataStore, ground_truth: GroundTruthUser) -> dict[str, float]:
    """Compute the genre distribution for the ground-truth user's relevant movies.

    Returns a dict mapping genre name → fraction of the user's relevant movies
    that include that genre.
    """
    genre_counts: dict[str, int] = {}
    total_movies = len(ground_truth.relevant_movie_ids)

    if total_movies == 0:
        return {}

    for movie_id in ground_truth.relevant_movie_ids:
        movie = data.get_movie(movie_id)
        if movie and movie.get("genres"):
            for genre in movie["genres"].split("|"):
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Convert counts to fractions, sorted by frequency
    distribution = {genre: round(count / total_movies, 2) for genre, count in genre_counts.items()}
    return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
