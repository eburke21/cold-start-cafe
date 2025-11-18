"""Pydantic models for the challenge mode API endpoints."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import AlgorithmName
from app.models.simulation import Demographics, MovieRecommendation, Rating

# --- Domain models ---


class ChallengeState(BaseModel):
    """Full in-memory state of a challenge mode session."""

    session_id: UUID = Field(default_factory=uuid4)
    target_user_id: int
    seed_ratings: list[Rating]
    demographics: Demographics
    user_picks: list[int] = Field(default_factory=list)
    ground_truth_top_movies: list[int] = Field(default_factory=list)


# --- API request/response models ---


class ChallengeTargetUser(BaseModel):
    """Info revealed to the challenger about the target user."""

    demographics: Demographics
    seed_ratings: list[MovieRecommendation]


class CreateChallengeResponse(BaseModel):
    """Response for POST /api/v1/challenge."""

    session_id: UUID
    target_user: ChallengeTargetUser
    available_movies: list[MovieRecommendation]


class SubmitChallengeRequest(BaseModel):
    """Request for POST /api/v1/challenge/{session_id}/submit."""

    picks: list[int] = Field(min_length=10, max_length=10)


class MetricScores(BaseModel):
    """Precision/recall/NDCG scores for a single scorer."""

    precision_at_10: float
    recall_at_10: float
    ndcg_at_10: float


class AlgorithmScore(BaseModel):
    """Scores for a single algorithm in challenge comparison."""

    algorithm: AlgorithmName
    precision_at_10: float
    ndcg_at_10: float


class SubmitChallengeResponse(BaseModel):
    """Response for POST /api/v1/challenge/{session_id}/submit."""

    user_score: MetricScores
    algorithm_scores: list[AlgorithmScore]
    narration: str
    ground_truth_favorites: list[MovieRecommendation]
