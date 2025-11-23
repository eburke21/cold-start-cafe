"""API routes for the simulation endpoints.

POST /api/v1/simulation           — Create a new simulation session
POST /api/v1/simulation/{id}/signal — Add a signal and re-run algorithms
GET  /api/v1/simulation/{id}      — Get full simulation state
"""

import random

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from app.models.simulation import (
    AddSignalRequest,
    AddSignalResponse,
    CreateSimulationResponse,
    CurrentSignals,
    GetSimulationResponse,
    MovieRecommendation,
)
from app.services.ground_truth import GroundTruthUser, select_ground_truth_user
from app.services.session_manager import SessionManager
from app.services.simulation_engine import (
    apply_signal,
    get_genre_distribution,
    run_step,
)
from app.services.validators import validate_signal

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["simulation"])

# Module-level session manager and ground-truth store.
# These are initialized during app startup via `init_simulation_router`.
_session_manager: SessionManager | None = None
_ground_truth_store: dict[str, GroundTruthUser] = {}


def init_simulation_router(session_manager: SessionManager) -> None:
    """Called during app startup to inject the session manager."""
    global _session_manager
    _session_manager = session_manager


def get_ground_truth_store() -> dict[str, GroundTruthUser]:
    """Expose the ground-truth store for other routers (e.g. narration)."""
    return _ground_truth_store


def _get_session_manager() -> SessionManager:
    if _session_manager is None:
        raise RuntimeError("Session manager not initialized")
    return _session_manager


@router.post(
    "/simulation",
    response_model=CreateSimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_simulation(request: Request):
    """Create a new simulation session with zero signals.

    Selects a random ground-truth user, runs all four algorithms with
    zero signals (step 0), and returns the initial results.
    """
    session_manager = _get_session_manager()
    data = request.app.state.data

    # Create session
    try:
        state = session_manager.create_session()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    # Select ground-truth user
    ground_truth = select_ground_truth_user(data)
    state.ground_truth_user_id = ground_truth.user_id
    _ground_truth_store[str(state.session_id)] = ground_truth

    logger.info(
        "Simulation created",
        session_id=str(state.session_id),
        ground_truth_user_id=ground_truth.user_id,
        relevant_movies=len(ground_truth.relevant_movie_ids),
    )

    # Run step 0 (zero signals)
    step = run_step(state, data, ground_truth, signal=None)
    state.steps.append(step)

    # Compute genre distribution for the ground-truth user
    genre_distribution = get_genre_distribution(data, ground_truth)

    # Sample some movies for the frontend to display
    sample_movies = _get_movie_sample(data)

    return CreateSimulationResponse(
        session_id=state.session_id,
        ground_truth_genre_distribution=genre_distribution,
        step=step,
        available_movies_sample=sample_movies,
    )


@router.post(
    "/simulation/{session_id}/signal",
    response_model=AddSignalResponse,
)
async def add_signal(session_id: str, signal_request: AddSignalRequest, request: Request):
    """Add a signal to the simulation and re-run all algorithms.

    Validates the signal, applies it to the state, runs all four algorithms,
    computes metrics, and returns the new step.
    """
    session_manager = _get_session_manager()
    data = request.app.state.data

    # Look up session
    from uuid import UUID

    try:
        sid = UUID(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid session ID format: {session_id}",
        ) from e

    state = session_manager.get_session(sid)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    ground_truth = _ground_truth_store.get(session_id)
    if ground_truth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ground truth not found for session {session_id}",
        )

    # Validate signal against dataset
    try:
        validate_signal(signal_request, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Apply signal to state
    try:
        signal = apply_signal(state, signal_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Run algorithms and produce step
    step = run_step(state, data, ground_truth, signal=signal)
    state.steps.append(step)

    logger.info(
        "Signal added",
        session_id=session_id,
        signal_type=signal_request.type,
        step_number=step.step_number,
    )

    return AddSignalResponse(step=step)


@router.get(
    "/simulation/{session_id}",
    response_model=GetSimulationResponse,
)
async def get_simulation(session_id: str):
    """Get the full simulation state with all steps."""
    session_manager = _get_session_manager()

    from uuid import UUID

    try:
        sid = UUID(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid session ID format: {session_id}",
        ) from e

    state = session_manager.get_session(sid)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    current_signals = CurrentSignals(
        ratings_count=len(state.ratings),
        has_demographics=(
            state.demographics.age is not None
            or state.demographics.gender is not None
            or state.demographics.occupation is not None
        ),
        genre_preferences=state.genre_preferences,
        view_history_count=len(state.view_history),
    )

    return GetSimulationResponse(
        session_id=state.session_id,
        steps=state.steps,
        current_signals=current_signals,
    )


def _get_movie_sample(data, count: int = 20) -> list[MovieRecommendation]:
    """Get a random sample of movies for the frontend to display."""
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
