"""Pydantic models for the simulation API endpoints."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import AlgorithmName, SignalType

# --- Domain models ---


class Rating(BaseModel):
    """A single movie rating by the simulated user."""

    movie_id: int
    score: float = Field(ge=1.0, le=5.0)


class Demographics(BaseModel):
    """Demographic info for the simulated user."""

    age: int | None = None
    gender: str | None = None
    occupation: str | None = None


class Signal(BaseModel):
    """A signal added at a specific simulation step."""

    type: SignalType
    step: int
    payload: dict


class MovieRecommendation(BaseModel):
    """A single recommended movie with metadata."""

    movie_id: int
    title: str
    genres: str
    score: float | None = None


class AlgorithmResult(BaseModel):
    """Results from one algorithm for a single simulation step."""

    algorithm: AlgorithmName
    recommendations: list[MovieRecommendation]
    precision_at_10: float
    recall_at_10: float
    ndcg_at_10: float


class SimulationStep(BaseModel):
    """A single step in the simulation timeline."""

    step_number: int
    signal_added: Signal | None = None
    results: list[AlgorithmResult]
    narration: str
    narration_source: str = "template"  # "template" or "llm"


class SimulationState(BaseModel):
    """Full in-memory state of an active simulation session."""

    session_id: UUID = Field(default_factory=uuid4)
    ratings: list[Rating] = Field(default_factory=list)
    demographics: Demographics = Field(default_factory=Demographics)
    genre_preferences: list[str] = Field(default_factory=list)
    view_history: list[int] = Field(default_factory=list)
    steps: list[SimulationStep] = Field(default_factory=list)
    ground_truth_user_id: int | None = None


# --- API request/response models ---


class CreateSimulationResponse(BaseModel):
    """Response for POST /api/v1/simulation."""

    session_id: UUID
    ground_truth_genre_distribution: dict[str, float]
    step: SimulationStep
    available_movies_sample: list[MovieRecommendation]


class AddSignalRequest(BaseModel):
    """Request for POST /api/v1/simulation/{session_id}/signal."""

    type: SignalType
    payload: dict


class AddSignalResponse(BaseModel):
    """Response for POST /api/v1/simulation/{session_id}/signal."""

    step: SimulationStep


class CurrentSignals(BaseModel):
    """Summary of signals currently in the simulation."""

    ratings_count: int
    has_demographics: bool
    genre_preferences: list[str]
    view_history_count: int


class GetSimulationResponse(BaseModel):
    """Response for GET /api/v1/simulation/{session_id}."""

    session_id: UUID
    steps: list[SimulationStep]
    current_signals: CurrentSignals
