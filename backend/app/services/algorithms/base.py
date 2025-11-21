"""Shared interface and result model for all recommendation algorithms."""

from typing import Protocol

from pydantic import BaseModel

from app.data.loader import DataStore
from app.models.simulation import SimulationState


class RecommenderResult(BaseModel):
    """Output from a recommendation algorithm.

    Attributes:
        movie_ids: Ranked list of recommended movie IDs (best first, up to 10).
        scores: Normalized scores in [0, 1] corresponding to each movie_id.
    """

    movie_ids: list[int]
    scores: list[float]


class Recommender(Protocol):
    """Protocol that every recommendation algorithm must satisfy.

    Algorithms are stateless functions: given the current simulation state
    (the simulated user's signals) and the DataStore (the MovieLens dataset),
    they return a ranked list of movie recommendations.
    """

    def __call__(self, state: SimulationState, data: DataStore) -> RecommenderResult: ...
