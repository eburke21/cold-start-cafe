"""Enumerations used across the API."""

from enum import StrEnum


class SignalType(StrEnum):
    """Types of signals a user can add to a simulation."""

    RATING = "rating"
    DEMOGRAPHIC = "demographic"
    GENRE_PREFERENCE = "genre_preference"
    VIEW_HISTORY = "view_history"


class AlgorithmName(StrEnum):
    """Names of the four recommendation algorithms."""

    POPULARITY = "popularity"
    CONTENT_BASED = "content_based"
    COLLABORATIVE = "collaborative"
    HYBRID = "hybrid"
