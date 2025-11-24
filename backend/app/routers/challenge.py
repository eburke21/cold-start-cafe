"""API routes for the challenge mode endpoints.

POST /api/v1/challenge                    — Create a new challenge session
POST /api/v1/challenge/{session_id}/submit — Submit 10 movie picks and get scores
"""

import random
import time
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from app.models.challenge import (
    ChallengeState,
    ChallengeTargetUser,
    CreateChallengeResponse,
    SubmitChallengeRequest,
    SubmitChallengeResponse,
)
from app.models.simulation import MovieRecommendation
from app.services.challenge_engine import (
    build_challenge_state,
    get_ground_truth_favorites,
    get_seed_ratings,
    get_user_demographics,
    run_algorithms_for_challenge,
    score_user_picks,
    select_challenge_user,
)
from app.services.ground_truth import GroundTruthUser
from app.services.narration.challenge_narrator import generate_challenge_narration

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["challenge"])

# Module-level challenge state store (UUID → ChallengeState)
_challenge_store: dict[str, ChallengeState] = {}
# Ground-truth store for challenges (UUID → GroundTruthUser)
_challenge_ground_truth: dict[str, GroundTruthUser] = {}
# Algorithm scores computed at creation time (UUID → list[AlgorithmScore])
_challenge_algo_scores: dict[str, list] = {}
# Creation timestamps for TTL eviction
_challenge_created_at: dict[str, float] = {}


@router.post(
    "/challenge",
    response_model=CreateChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_challenge(request: Request):
    """Create a new challenge session.

    Selects a ground-truth user with ≥30 ratings, reveals their demographics
    and 3 seed ratings, runs all four algorithms with the seed data, and
    returns the challenge setup for the frontend.
    """
    data = request.app.state.data

    # Select a challenge-worthy user (≥30 ratings)
    ground_truth = select_challenge_user(data)

    # Get seed ratings and demographics
    seed_ratings = get_seed_ratings(data, ground_truth)
    demographics = get_user_demographics(data, ground_truth.user_id)

    # Build challenge state
    challenge_state = build_challenge_state(ground_truth, seed_ratings, demographics)
    session_id = str(challenge_state.session_id)

    # Run algorithms with seed data (scores stored for later comparison)
    algo_scores = run_algorithms_for_challenge(seed_ratings, demographics, data, ground_truth)

    # Store everything server-side
    _challenge_store[session_id] = challenge_state
    _challenge_ground_truth[session_id] = ground_truth
    _challenge_algo_scores[session_id] = algo_scores
    _challenge_created_at[session_id] = time.time()

    logger.info(
        "Challenge created",
        session_id=session_id,
        target_user_id=ground_truth.user_id,
        relevant_movies=len(ground_truth.relevant_movie_ids),
    )

    # Build target user info for the frontend
    seed_movie_recs = []
    for rating in seed_ratings:
        movie = data.get_movie(rating.movie_id)
        if movie:
            seed_movie_recs.append(
                MovieRecommendation(
                    movie_id=rating.movie_id,
                    title=movie["title"],
                    genres=movie.get("genres", ""),
                    score=rating.score,
                )
            )

    target_user = ChallengeTargetUser(
        demographics=demographics,
        seed_ratings=seed_movie_recs,
    )

    # Provide a sample of movies for the user to browse
    available_movies = _get_browseable_movies(data)

    return CreateChallengeResponse(
        session_id=challenge_state.session_id,
        target_user=target_user,
        available_movies=available_movies,
    )


@router.post(
    "/challenge/{session_id}/submit",
    response_model=SubmitChallengeResponse,
)
async def submit_challenge(session_id: str, body: SubmitChallengeRequest, request: Request):
    """Submit 10 movie picks and get the challenge results.

    Computes the user's precision@10, recall@10, NDCG@10 against the
    ground-truth relevant set, compares with algorithm scores, generates
    narration, and reveals the ground-truth favorites.
    """
    data = request.app.state.data

    # Validate session
    try:
        UUID(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid session ID format: {session_id}",
        ) from e

    challenge_state = _challenge_store.get(session_id)
    if challenge_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge session {session_id} not found",
        )

    ground_truth = _challenge_ground_truth.get(session_id)
    if ground_truth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ground truth not found for challenge {session_id}",
        )

    # Validate picks
    picks = body.picks
    if len(set(picks)) != len(picks):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate movie IDs in picks",
        )

    # Validate all movie IDs exist
    for movie_id in picks:
        if data.get_movie(movie_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Movie with ID {movie_id} not found in catalog",
            )

    # Score the user's picks
    user_score = score_user_picks(picks, ground_truth)

    # Retrieve pre-computed algorithm scores
    algo_scores = _challenge_algo_scores.get(session_id, [])

    # Generate narration comparing user vs. algorithms
    narration = await generate_challenge_narration(
        demographics=challenge_state.demographics,
        seed_ratings=challenge_state.seed_ratings,
        user_picks=picks,
        user_score=user_score,
        algo_scores=algo_scores,
        data=data,
    )

    # Get ground-truth favorites for the reveal
    favorites = get_ground_truth_favorites(data, ground_truth)

    # Store the user's picks
    challenge_state.user_picks = picks

    logger.info(
        "Challenge submitted",
        session_id=session_id,
        user_precision=user_score.precision_at_10,
        user_ndcg=user_score.ndcg_at_10,
    )

    return SubmitChallengeResponse(
        user_score=user_score,
        algorithm_scores=algo_scores,
        narration=narration,
        ground_truth_favorites=favorites,
    )


def _get_browseable_movies(data, count: int = 50) -> list[MovieRecommendation]:
    """Get a random sample of movies for the challenge picker.

    Returns more movies than the simulation sample (50 vs 20) since
    the user needs to browse and pick 10.
    """
    movies_df = data.movies_df
    sample_size = min(count, len(movies_df))
    sample_indices = random.sample(range(len(movies_df)), sample_size)

    movies = []
    for idx in sample_indices:
        row = movies_df.iloc[idx]
        movies.append(
            MovieRecommendation(
                movie_id=int(row["movie_id"]),
                title=str(row["title"]),
                genres=str(row.get("genres", "")),
                score=None,
            )
        )
    return movies


def evict_expired_challenges(ttl_seconds: int) -> int:
    """Remove challenge sessions older than the given TTL.

    Args:
        ttl_seconds: Maximum session age in seconds.

    Returns:
        Number of sessions evicted.
    """
    now = time.time()
    cutoff = now - ttl_seconds
    expired = [sid for sid, created in _challenge_created_at.items() if created < cutoff]

    for sid in expired:
        _challenge_store.pop(sid, None)
        _challenge_ground_truth.pop(sid, None)
        _challenge_algo_scores.pop(sid, None)
        _challenge_created_at.pop(sid, None)

    if expired:
        logger.info(
            "Evicted expired challenge sessions",
            count=len(expired),
            ttl_seconds=ttl_seconds,
        )

    return len(expired)
