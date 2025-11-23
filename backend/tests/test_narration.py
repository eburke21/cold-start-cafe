"""Tests for the narration system.

Covers:
- Template matcher logic (priority order, deduplication)
- Template loading from JSON
- LLM fallback narration strings
- Integration with simulation engine (narration_source field)
"""

import json
from pathlib import Path

import pytest

from app.models.enums import AlgorithmName, SignalType
from app.models.simulation import (
    AlgorithmResult,
    Demographics,
    Rating,
    Signal,
    SimulationState,
    SimulationStep,
)
from app.services.narration.llm_narrator import _fallback_narration
from app.services.narration.templates import _load_templates, match_template


# --- Fixtures ---


def _make_step(
    step_number: int,
    signal: Signal | None = None,
    narration: str = "",
    results: list[AlgorithmResult] | None = None,
) -> SimulationStep:
    """Create a SimulationStep with sensible defaults."""
    if results is None:
        results = [
            AlgorithmResult(
                algorithm=AlgorithmName.POPULARITY,
                recommendations=[],
                precision_at_10=0.1,
                recall_at_10=0.05,
                ndcg_at_10=0.08,
            ),
            AlgorithmResult(
                algorithm=AlgorithmName.CONTENT_BASED,
                recommendations=[],
                precision_at_10=0.1,
                recall_at_10=0.05,
                ndcg_at_10=0.08,
            ),
            AlgorithmResult(
                algorithm=AlgorithmName.COLLABORATIVE,
                recommendations=[],
                precision_at_10=0.1,
                recall_at_10=0.05,
                ndcg_at_10=0.08,
            ),
            AlgorithmResult(
                algorithm=AlgorithmName.HYBRID,
                recommendations=[],
                precision_at_10=0.1,
                recall_at_10=0.05,
                ndcg_at_10=0.08,
            ),
        ]
    return SimulationStep(
        step_number=step_number,
        signal_added=signal,
        results=results,
        narration=narration,
    )


def _make_state(**kwargs) -> SimulationState:
    """Create a SimulationState with optional overrides."""
    defaults = {
        "ratings": [],
        "demographics": Demographics(),
        "genre_preferences": [],
        "view_history": [],
        "steps": [],
    }
    defaults.update(kwargs)
    return SimulationState(**defaults)


# --- Template Loading ---


class TestTemplateLoading:
    """Verify narration templates load correctly from JSON."""

    def test_templates_load_successfully(self):
        """Templates JSON file exists and loads with expected keys."""
        templates = _load_templates()
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_required_template_keys_exist(self):
        """All template keys referenced by the matcher exist in the JSON."""
        templates = _load_templates()
        required_keys = [
            "cold_start_intro",
            "first_rating",
            "second_rating",
            "three_ratings",
            "five_ratings",
            "many_ratings",
            "demographics_added",
            "genre_prefs_set",
            "view_history_added",
            "hybrid_leads",
            "all_signals_combined",
        ]
        for key in required_keys:
            assert key in templates, f"Missing template key: {key}"

    def test_template_values_are_nonempty_strings(self):
        """Every template value should be a non-empty string."""
        templates = _load_templates()
        for key, value in templates.items():
            assert isinstance(value, str), f"Template '{key}' is not a string"
            assert len(value) > 0, f"Template '{key}' is empty"


# --- Template Matcher ---


class TestTemplateMatcherStepZero:
    """Step 0 always gets the cold-start intro template."""

    def test_step_zero_returns_cold_start_intro(self):
        state = _make_state()
        step = _make_step(step_number=0)
        result = match_template(state, step)
        assert result is not None
        assert "cold-start" in result.lower() or "cold start" in result.lower()


class TestTemplateMatcherRatings:
    """Template matching for rating signals at various counts."""

    def test_first_rating(self):
        state = _make_state(ratings=[Rating(movie_id=1, score=4.0)])
        signal = Signal(
            type=SignalType.RATING,
            step=1,
            payload={"movie_id": 1, "score": 4.0},
        )
        step = _make_step(step_number=1, signal=signal)
        result = match_template(state, step)
        assert result is not None
        templates = _load_templates()
        assert result == templates["first_rating"]

    def test_second_rating(self):
        state = _make_state(
            ratings=[
                Rating(movie_id=1, score=4.0),
                Rating(movie_id=2, score=3.0),
            ]
        )
        signal = Signal(
            type=SignalType.RATING,
            step=2,
            payload={"movie_id": 2, "score": 3.0},
        )
        step = _make_step(step_number=2, signal=signal)
        result = match_template(state, step)
        assert result is not None
        templates = _load_templates()
        assert result == templates["second_rating"]

    def test_three_ratings(self):
        state = _make_state(
            ratings=[
                Rating(movie_id=i, score=4.0) for i in range(1, 4)
            ]
        )
        signal = Signal(
            type=SignalType.RATING,
            step=3,
            payload={"movie_id": 3, "score": 4.0},
        )
        step = _make_step(step_number=3, signal=signal)
        result = match_template(state, step)
        templates = _load_templates()
        assert result == templates["three_ratings"]

    def test_four_ratings_falls_through_to_llm(self):
        """4 ratings has no specific template — should return None for LLM."""
        state = _make_state(
            ratings=[Rating(movie_id=i, score=4.0) for i in range(1, 5)]
        )
        signal = Signal(
            type=SignalType.RATING,
            step=4,
            payload={"movie_id": 4, "score": 4.0},
        )
        step = _make_step(step_number=4, signal=signal)
        result = match_template(state, step)
        assert result is None

    def test_five_ratings(self):
        state = _make_state(
            ratings=[Rating(movie_id=i, score=4.0) for i in range(1, 6)]
        )
        signal = Signal(
            type=SignalType.RATING,
            step=5,
            payload={"movie_id": 5, "score": 4.0},
        )
        step = _make_step(step_number=5, signal=signal)
        result = match_template(state, step)
        templates = _load_templates()
        assert result == templates["five_ratings"]


class TestTemplateMatcherSignalTypes:
    """Template matching for non-rating signal types."""

    def test_demographics_signal(self):
        state = _make_state(
            demographics=Demographics(age=25, gender="M", occupation="student")
        )
        signal = Signal(
            type=SignalType.DEMOGRAPHIC,
            step=1,
            payload={"age": 25, "gender": "M", "occupation": "student"},
        )
        step = _make_step(step_number=1, signal=signal)
        result = match_template(state, step)
        templates = _load_templates()
        assert result == templates["demographics_added"]

    def test_genre_preference_signal(self):
        state = _make_state(genre_preferences=["Action", "Comedy"])
        signal = Signal(
            type=SignalType.GENRE_PREFERENCE,
            step=1,
            payload={"genres": ["Action", "Comedy"]},
        )
        step = _make_step(step_number=1, signal=signal)
        result = match_template(state, step)
        templates = _load_templates()
        assert result == templates["genre_prefs_set"]

    def test_view_history_signal(self):
        state = _make_state(view_history=[1, 2, 3])
        signal = Signal(
            type=SignalType.VIEW_HISTORY,
            step=1,
            payload={"movie_ids": [1, 2, 3]},
        )
        step = _make_step(step_number=1, signal=signal)
        result = match_template(state, step)
        templates = _load_templates()
        assert result == templates["view_history_added"]


class TestTemplateMatcherDeduplication:
    """Templates that should only fire once per session."""

    def test_many_ratings_fires_once(self):
        """'many_ratings' template fires at 10+ ratings, but not again."""
        templates = _load_templates()
        many_ratings_text = templates["many_ratings"]

        # First time at 10 ratings — should match
        state = _make_state(
            ratings=[Rating(movie_id=i, score=4.0) for i in range(1, 11)]
        )
        signal = Signal(
            type=SignalType.RATING,
            step=10,
            payload={"movie_id": 10, "score": 4.0},
        )
        step = _make_step(step_number=10, signal=signal)
        result = match_template(state, step)
        assert result == many_ratings_text

        # Now add that step (with the template narration) to history
        step.narration = many_ratings_text
        state.steps.append(step)

        # 11th rating — many_ratings already used, should return None
        state.ratings.append(Rating(movie_id=11, score=3.5))
        signal2 = Signal(
            type=SignalType.RATING,
            step=11,
            payload={"movie_id": 11, "score": 3.5},
        )
        step2 = _make_step(step_number=11, signal=signal2)
        result2 = match_template(state, step2)
        assert result2 is None


class TestTemplateMatcherHybridLeads:
    """Hybrid algorithm leading triggers a special template."""

    def test_hybrid_leads_when_best_precision(self):
        """When hybrid has highest precision, fire the hybrid_leads template."""
        results = [
            AlgorithmResult(
                algorithm=AlgorithmName.POPULARITY,
                recommendations=[],
                precision_at_10=0.1,
                recall_at_10=0.05,
                ndcg_at_10=0.08,
            ),
            AlgorithmResult(
                algorithm=AlgorithmName.CONTENT_BASED,
                recommendations=[],
                precision_at_10=0.15,
                recall_at_10=0.10,
                ndcg_at_10=0.12,
            ),
            AlgorithmResult(
                algorithm=AlgorithmName.COLLABORATIVE,
                recommendations=[],
                precision_at_10=0.12,
                recall_at_10=0.08,
                ndcg_at_10=0.10,
            ),
            AlgorithmResult(
                algorithm=AlgorithmName.HYBRID,
                recommendations=[],
                precision_at_10=0.25,  # Highest
                recall_at_10=0.15,
                ndcg_at_10=0.20,
            ),
        ]
        # Use a rating signal (no specific template at 4 ratings)
        state = _make_state(
            ratings=[Rating(movie_id=i, score=4.0) for i in range(1, 5)]
        )
        signal = Signal(
            type=SignalType.RATING,
            step=4,
            payload={"movie_id": 4, "score": 4.0},
        )
        step = _make_step(step_number=4, signal=signal, results=results)
        result = match_template(state, step)
        templates = _load_templates()
        assert result == templates["hybrid_leads"]


# --- LLM Fallback ---


class TestFallbackNarration:
    """Verify the LLM fallback narration generator."""

    def test_fallback_with_signal(self):
        """Fallback narration includes signal type and step number."""
        signal = Signal(
            type=SignalType.RATING,
            step=3,
            payload={"movie_id": 1, "score": 5.0},
        )
        step = _make_step(step_number=3, signal=signal)
        result = _fallback_narration(step)
        assert "rating" in result.lower()
        assert "step 3" in result.lower()

    def test_fallback_without_signal(self):
        """Fallback narration for a step with no signal."""
        step = _make_step(step_number=0)
        result = _fallback_narration(step)
        assert "step 0" in result.lower()

    def test_fallback_returns_nonempty_string(self):
        """Fallback should always return something meaningful."""
        step = _make_step(step_number=5)
        result = _fallback_narration(step)
        assert isinstance(result, str)
        assert len(result) > 10


# --- Narration Source Integration ---


class TestNarrationSource:
    """Verify the narration_source field is set correctly."""

    def test_step_defaults_to_template_source(self):
        """SimulationStep defaults narration_source to 'template'."""
        step = _make_step(step_number=0)
        assert step.narration_source == "template"

    def test_step_accepts_llm_source(self):
        """SimulationStep can be set to 'llm' source."""
        step = SimulationStep(
            step_number=1,
            signal_added=None,
            results=[],
            narration="Generating...",
            narration_source="llm",
        )
        assert step.narration_source == "llm"
