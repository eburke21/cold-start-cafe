"""Input validation for simulation signals.

Validates signal payloads against the DataStore to ensure movie IDs exist,
genres are valid, rating scores are in range, etc. Raises ValueError with
descriptive messages for the error handler to convert to 400 responses.
"""

from app.data.loader import DataStore
from app.models.enums import SignalType
from app.models.simulation import AddSignalRequest

# MovieLens 100K rating scale: 1-5 in 1.0 increments
VALID_SCORES = {1.0, 2.0, 3.0, 4.0, 5.0}


def _get_valid_genres(data: DataStore) -> set[str]:
    """Extract all unique genre names from the movie catalog."""
    genres: set[str] = set()
    for genres_str in data.movies_df["genres"]:
        if genres_str and isinstance(genres_str, str):
            genres.update(genres_str.split("|"))
    return genres


def validate_signal(signal: AddSignalRequest, data: DataStore) -> None:
    """Validate a signal request against the dataset.

    Raises:
        ValueError: If the signal payload is invalid.
    """
    if signal.type == SignalType.RATING:
        _validate_rating(signal.payload, data)
    elif signal.type == SignalType.DEMOGRAPHIC:
        _validate_demographic(signal.payload)
    elif signal.type == SignalType.GENRE_PREFERENCE:
        _validate_genre_preference(signal.payload, data)
    elif signal.type == SignalType.VIEW_HISTORY:
        _validate_view_history(signal.payload, data)


def _validate_rating(payload: dict, data: DataStore) -> None:
    """Validate a rating signal payload."""
    movie_id = payload.get("movie_id")
    score = payload.get("score")

    if movie_id is None:
        raise ValueError("Rating signal requires 'movie_id' in payload")
    if score is None:
        raise ValueError("Rating signal requires 'score' in payload")

    # Check movie exists
    if data.get_movie(int(movie_id)) is None:
        raise ValueError(f"Movie with ID {movie_id} not found in catalog")

    # Check score is valid
    score_float = float(score)
    if score_float < 1.0 or score_float > 5.0:
        raise ValueError(f"Rating score must be between 1.0 and 5.0, got {score_float}")
    if score_float not in VALID_SCORES:
        raise ValueError(
            f"Rating score must be a whole number (1, 2, 3, 4, or 5), got {score_float}"
        )


def _validate_demographic(payload: dict) -> None:
    """Validate a demographic signal payload."""
    if not payload:
        raise ValueError("Demographic signal requires at least one field in payload")

    valid_fields = {"age", "gender", "occupation"}
    unknown_fields = set(payload.keys()) - valid_fields
    if unknown_fields:
        raise ValueError(f"Unknown demographic fields: {unknown_fields}")

    age = payload.get("age")
    if age is not None:
        age_int = int(age)
        if age_int < 1 or age_int > 120:
            raise ValueError(f"Age must be between 1 and 120, got {age_int}")

    gender = payload.get("gender")
    if gender is not None and gender not in ("M", "F"):
        raise ValueError(f"Gender must be 'M' or 'F', got '{gender}'")


def _validate_genre_preference(payload: dict, data: DataStore) -> None:
    """Validate a genre preference signal payload."""
    genres = payload.get("genres")
    if not genres or not isinstance(genres, list):
        raise ValueError("Genre preference signal requires 'genres' list in payload")

    valid_genres = _get_valid_genres(data)
    invalid = [g for g in genres if g not in valid_genres]
    if invalid:
        raise ValueError(f"Unknown genres: {invalid}. Valid genres: {sorted(valid_genres)}")


def _validate_view_history(payload: dict, data: DataStore) -> None:
    """Validate a view history signal payload."""
    movie_ids = payload.get("movie_ids")
    if not movie_ids or not isinstance(movie_ids, list):
        raise ValueError("View history signal requires 'movie_ids' list in payload")

    invalid = [mid for mid in movie_ids if data.get_movie(int(mid)) is None]
    if invalid:
        raise ValueError(f"Movie IDs not found in catalog: {invalid}")
