"""Pre-generated narration template matcher.

Examines the current simulation state and the latest step to determine
which pre-generated narration template to use. Returns None if no
template matches, signaling the LLM fallback path.
"""

import json
from pathlib import Path

import structlog

from app.models.enums import AlgorithmName, SignalType
from app.models.simulation import SimulationState, SimulationStep

logger = structlog.get_logger()

# Load templates once at module import time
_TEMPLATES_PATH = Path(__file__).parent.parent.parent / "data" / "narrations.json"
_TEMPLATES: dict[str, str] = {}


def _load_templates() -> dict[str, str]:
    """Load narration templates from JSON file."""
    global _TEMPLATES
    if not _TEMPLATES:
        with open(_TEMPLATES_PATH) as f:
            _TEMPLATES = json.load(f)
        logger.info("Loaded narration templates", count=len(_TEMPLATES))
    return _TEMPLATES


def _get_template(key: str) -> str | None:
    """Get a narration template by key."""
    templates = _load_templates()
    return templates.get(key)


def _has_used_template(state: SimulationState, template_key: str) -> bool:
    """Check if a specific template narration has already been used in this session.

    Compares narration text against the template to detect prior usage.
    """
    templates = _load_templates()
    template_text = templates.get(template_key)
    if not template_text:
        return False
    return any(step.narration == template_text for step in state.steps)


def match_template(state: SimulationState, step: SimulationStep) -> str | None:
    """Match the current simulation state to a pre-generated narration template.

    Checks conditions in priority order (most specific first).
    Returns the narration text if a template matches, or None for LLM fallback.

    Args:
        state: Full simulation state (including all previous steps).
        step: The step that was just computed (already has algorithm results).

    Returns:
        Narration text from a matching template, or None.
    """
    signal = step.signal_added
    ratings_count = len(state.ratings)

    # 1. Step 0 — cold start intro
    if step.step_number == 0:
        return _get_template("cold_start_intro")

    # 2. First rating ever added
    if signal and signal.type == SignalType.RATING and ratings_count == 1:
        return _get_template("first_rating")

    # 3. Second rating
    if signal and signal.type == SignalType.RATING and ratings_count == 2:
        return _get_template("second_rating")

    # 4. Three ratings
    if signal and signal.type == SignalType.RATING and ratings_count == 3:
        return _get_template("three_ratings")

    # 5. Five ratings
    if signal and signal.type == SignalType.RATING and ratings_count == 5:
        return _get_template("five_ratings")

    # 6. Many ratings (10+), only once
    if (
        signal
        and signal.type == SignalType.RATING
        and ratings_count >= 10
        and not _has_used_template(state, "many_ratings")
    ):
        return _get_template("many_ratings")

    # 7. Demographics just added
    if signal and signal.type == SignalType.DEMOGRAPHIC:
        return _get_template("demographics_added")

    # 8. Genre preferences just set
    if signal and signal.type == SignalType.GENRE_PREFERENCE:
        return _get_template("genre_prefs_set")

    # 9. View history just added
    if signal and signal.type == SignalType.VIEW_HISTORY:
        return _get_template("view_history_added")

    # 10. Check if all signal types have been provided
    has_ratings = ratings_count > 0
    has_demographics = (
        state.demographics.age is not None
        or state.demographics.gender is not None
        or state.demographics.occupation is not None
    )
    has_genres = len(state.genre_preferences) > 0
    has_history = len(state.view_history) > 0
    if (
        has_ratings
        and has_demographics
        and has_genres
        and has_history
        and not _has_used_template(state, "all_signals_combined")
    ):
        return _get_template("all_signals_combined")

    # 11. Hybrid algorithm leads all others for the first time
    if step.results:
        hybrid_result = next((r for r in step.results if r.algorithm == AlgorithmName.HYBRID), None)
        if hybrid_result:
            other_scores = [
                r.precision_at_10 for r in step.results if r.algorithm != AlgorithmName.HYBRID
            ]
            if other_scores and hybrid_result.precision_at_10 > max(other_scores):
                if not _has_used_template(state, "hybrid_leads"):
                    return _get_template("hybrid_leads")

    # No template matched — LLM fallback
    return None
