"""Pydantic models for the ColdStart Café API."""

from app.models.challenge import (
    AlgorithmScore,
    ChallengeState,
    ChallengeTargetUser,
    CreateChallengeResponse,
    MetricScores,
    SubmitChallengeRequest,
    SubmitChallengeResponse,
)
from app.models.enums import AlgorithmName, SignalType
from app.models.movies import MovieSearchResponse, MovieSearchResult
from app.models.simulation import (
    AddSignalRequest,
    AddSignalResponse,
    AlgorithmResult,
    CreateSimulationResponse,
    CurrentSignals,
    Demographics,
    GetSimulationResponse,
    MovieRecommendation,
    Rating,
    Signal,
    SimulationState,
    SimulationStep,
)

__all__ = [
    # Enums
    "AlgorithmName",
    "SignalType",
    # Simulation
    "AddSignalRequest",
    "AddSignalResponse",
    "AlgorithmResult",
    "CreateSimulationResponse",
    "CurrentSignals",
    "Demographics",
    "GetSimulationResponse",
    "MovieRecommendation",
    "Rating",
    "Signal",
    "SimulationState",
    "SimulationStep",
    # Challenge
    "AlgorithmScore",
    "ChallengeState",
    "ChallengeTargetUser",
    "CreateChallengeResponse",
    "MetricScores",
    "SubmitChallengeRequest",
    "SubmitChallengeResponse",
    # Movies
    "MovieSearchResponse",
    "MovieSearchResult",
]
