"""Challenge mode scoring engine.

Takes the user's 10 movie picks, computes precision@10, recall@10, NDCG@10
against the ground-truth relevant set, and compares against the four
algorithms' scores (already computed at challenge creation time).
"""

import random
import time

import structlog

from app.data.loader import DataStore
from app.models.challenge import (
    AlgorithmScore,
    ChallengeState,
    MetricScores,
)
from app.models.enums import AlgorithmName
from app.models.simulation import (
    Demographics,
    MovieRecommendation,
    Rating,
    SimulationState,
)
from app.services.algorithms import collaborative, content_based, hybrid, popularity
from app.services.algorithms.base import RecommenderResult
from app.services.ground_truth import GroundTruthUser
from app.services.metrics import ndcg_at_k, precision_at_k, recall_at_k

logger = structlog.get_logger()


def select_challenge_user(data: DataStore, min_ratings: int = 30) -> GroundTruthUser:
    """Select a ground-truth user suitable for the challenge.

    Challenge users need more ratings (≥30) than simulation users (≥20)
    to ensure a richer challenge with enough high-rated movies to
    make the relevant set meaningful.

    Args:
        data: The DataStore with MovieLens data loaded.
        min_ratings: Minimum number of ratings required.

    Returns:
        A GroundTruthUser with relevant set and all rated movies.

    Raises:
        ValueError: If no eligible users are found.
    """
    eligible = data.get_eligible_ground_truth_users(min_genres=3, min_ratings=min_ratings)
    if not eligible:
        raise ValueError("No eligible challenge users found in dataset")

    user_id = random.choice(eligible)

    user_ratings = data.ratings_df[data.ratings_df["user_id"] == user_id]
    relevant = set(user_ratings[user_ratings["rating"] >= 4.0]["movie_id"].tolist())
    all_rated = set(user_ratings["movie_id"].tolist())

    return GroundTruthUser(
        user_id=user_id,
        relevant_movie_ids=relevant,
        all_rated_movie_ids=all_rated,
    )


def get_seed_ratings(
    data: DataStore, ground_truth: GroundTruthUser, count: int = 3
) -> list[Rating]:
    """Pick random seed ratings from the user's highly rated movies.

    These are revealed to the challenger as clues about the target user's
    taste. Only movies rated 4.0+ are eligible.

    Args:
        data: The DataStore with MovieLens data loaded.
        ground_truth: The challenge target user.
        count: Number of seed ratings to reveal.

    Returns:
        A list of Rating objects with movie_id and score.
    """
    user_ratings = data.ratings_df[data.ratings_df["user_id"] == ground_truth.user_id]
    high_rated = user_ratings[user_ratings["rating"] >= 4.0]

    if len(high_rated) <= count:
        sample = high_rated
    else:
        sample = high_rated.sample(n=count)

    return [
        Rating(movie_id=int(row["movie_id"]), score=float(row["rating"]))
        for _, row in sample.iterrows()
    ]


def get_user_demographics(data: DataStore, user_id: int) -> Demographics:
    """Look up the demographics for a MovieLens user.

    Args:
        data: The DataStore with user data loaded.
        user_id: The MovieLens user ID.

    Returns:
        A Demographics object with age, gender, and occupation.
    """
    user_row = data.users_df[data.users_df["user_id"] == user_id]
    if user_row.empty:
        return Demographics()

    row = user_row.iloc[0]
    return Demographics(
        age=int(row["age"]) if "age" in row else None,
        gender=str(row["gender"]) if "gender" in row else None,
        occupation=str(row["occupation"]) if "occupation" in row else None,
    )


def run_algorithms_for_challenge(
    seed_ratings: list[Rating],
    demographics: Demographics,
    data: DataStore,
    ground_truth: GroundTruthUser,
) -> list[AlgorithmScore]:
    """Run all four algorithms using the seed ratings and demographics.

    Builds a minimal SimulationState from the seed data, runs each algorithm,
    and computes metrics against the ground-truth relevant set.

    Args:
        seed_ratings: The 3 seed ratings revealed to the challenger.
        demographics: The target user's demographics.
        data: The DataStore with MovieLens data loaded.
        ground_truth: The challenge target user.

    Returns:
        A list of AlgorithmScore objects with precision@10 and NDCG@10.
    """
    start_time = time.time()

    # Build a minimal simulation state from seed data
    state = SimulationState(
        ratings=seed_ratings,
        demographics=demographics,
    )

    algorithms = [
        (AlgorithmName.POPULARITY, popularity.recommend),
        (AlgorithmName.CONTENT_BASED, content_based.recommend),
        (AlgorithmName.COLLABORATIVE, collaborative.recommend),
        (AlgorithmName.HYBRID, hybrid.recommend),
    ]

    scores = []
    for name, recommend_fn in algorithms:
        result: RecommenderResult = recommend_fn(state, data)
        p_at_10 = precision_at_k(result.movie_ids, ground_truth.relevant_movie_ids)
        n_at_10 = ndcg_at_k(result.movie_ids, ground_truth.relevant_movie_ids)

        scores.append(
            AlgorithmScore(
                algorithm=name,
                precision_at_10=round(p_at_10, 4),
                ndcg_at_10=round(n_at_10, 4),
            )
        )

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(
        "Challenge algorithms computed",
        computation_time_ms=round(elapsed_ms, 1),
    )

    return scores


def score_user_picks(
    user_picks: list[int],
    ground_truth: GroundTruthUser,
) -> MetricScores:
    """Score the user's 10 movie picks against the ground-truth relevant set.

    Args:
        user_picks: The user's list of 10 movie IDs.
        ground_truth: The challenge target user.

    Returns:
        MetricScores with precision@10, recall@10, NDCG@10.
    """
    return MetricScores(
        precision_at_10=round(precision_at_k(user_picks, ground_truth.relevant_movie_ids), 4),
        recall_at_10=round(recall_at_k(user_picks, ground_truth.relevant_movie_ids), 4),
        ndcg_at_10=round(ndcg_at_k(user_picks, ground_truth.relevant_movie_ids), 4),
    )


def get_ground_truth_favorites(
    data: DataStore,
    ground_truth: GroundTruthUser,
    limit: int = 10,
) -> list[MovieRecommendation]:
    """Get the target user's actual favorite movies for the reveal.

    Returns the top-rated movies sorted by rating (descending), then by
    movie_id for stable ordering.

    Args:
        data: The DataStore with MovieLens data loaded.
        ground_truth: The challenge target user.
        limit: Maximum number of favorites to return.

    Returns:
        A list of MovieRecommendation objects with score = user's rating.
    """
    user_ratings = data.ratings_df[data.ratings_df["user_id"] == ground_truth.user_id]
    top_rated = user_ratings.sort_values(by=["rating", "movie_id"], ascending=[False, True]).head(
        limit
    )

    favorites = []
    for _, row in top_rated.iterrows():
        movie = data.get_movie(int(row["movie_id"]))
        if movie:
            favorites.append(
                MovieRecommendation(
                    movie_id=int(row["movie_id"]),
                    title=movie["title"],
                    genres=movie.get("genres", ""),
                    score=float(row["rating"]),
                )
            )
    return favorites


def build_challenge_state(
    ground_truth: GroundTruthUser,
    seed_ratings: list[Rating],
    demographics: Demographics,
) -> ChallengeState:
    """Create a new ChallengeState from the selected user and seed data.

    Args:
        ground_truth: The challenge target user.
        seed_ratings: The seed ratings to reveal.
        demographics: The target user's demographics.

    Returns:
        A ChallengeState ready to be stored in the session.
    """
    return ChallengeState(
        target_user_id=ground_truth.user_id,
        seed_ratings=seed_ratings,
        demographics=demographics,
        ground_truth_top_movies=sorted(ground_truth.relevant_movie_ids),
    )
