"""Claude API-powered narration fallback.

When no pre-generated template matches the current simulation state,
this module generates a dynamic narration by calling the Claude API
with streaming enabled. Yields text chunks as they arrive.
"""

from collections.abc import AsyncGenerator

import structlog

from app.config import settings
from app.models.simulation import SimulationState, SimulationStep

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are the warm, knowledgeable narrator of ColdStart Café — an interactive \
educational tool that demonstrates the cold-start problem in recommendation systems.

Your job is to narrate what just happened in the simulation in 2-3 concise sentences \
(under 80 words). Use a warm, café-themed voice. Explain what the signal means for \
each algorithm in plain language. \
Reference specific algorithm names (Popularity, Content-Based, Collaborative, Hybrid) and explain \
why metrics changed.

Do NOT use markdown, bullet points, or headers. Write in flowing prose. \
Be educational but conversational — like a friendly barista explaining how coffee is roasted."""


def _build_user_prompt(
    state: SimulationState,
    step: SimulationStep,
    previous_narrations: list[str],
) -> str:
    """Build the user prompt with simulation context."""
    # Signal summary
    signal_desc = "No signal (initial step)"
    if step.signal_added:
        signal_desc = f"Signal type: {step.signal_added.type}, payload: {step.signal_added.payload}"

    # Algorithm results summary
    results_summary = []
    for r in step.results:
        results_summary.append(
            f"  {r.algorithm}: P@10={r.precision_at_10:.3f}, "
            f"R@10={r.recall_at_10:.3f}, NDCG@10={r.ndcg_at_10:.3f}"
        )

    # State summary
    state_summary = (
        f"Ratings: {len(state.ratings)}, "
        f"Demographics: {'set' if state.demographics.age else 'not set'}, "
        f"Genre preferences: {len(state.genre_preferences)} genres, "
        f"View history: {len(state.view_history)} movies"
    )

    # Previous narrations for context
    prev_text = ""
    if previous_narrations:
        prev_text = "\n\nPrevious narrations (for context, don't repeat):\n"
        for narr in previous_narrations[-2:]:
            prev_text += f"- {narr[:100]}...\n" if len(narr) > 100 else f"- {narr}\n"

    return f"""Step {step.step_number} just completed.

Signal: {signal_desc}

Current state: {state_summary}

Algorithm results:
{chr(10).join(results_summary)}
{prev_text}
Narrate what just happened and what it means for the algorithms."""


async def generate_narration(
    state: SimulationState,
    step: SimulationStep,
    previous_narrations: list[str],
) -> AsyncGenerator[str, None]:
    """Generate a streaming narration using the Claude API.

    Yields text chunks as they arrive from the API.
    On error, yields a generic fallback string.

    Args:
        state: Current simulation state.
        step: The step that was just computed.
        previous_narrations: List of narration strings from previous steps.

    Yields:
        Text chunks from the Claude API response.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY set, using fallback narration")
        yield _fallback_narration(step)
        return

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        user_prompt = _build_user_prompt(state, step, previous_narrations)

        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    except Exception as e:
        logger.error("LLM narration failed", error=str(e), step=step.step_number)
        yield _fallback_narration(step)


def _fallback_narration(step: SimulationStep) -> str:
    """Generate a generic fallback narration when the LLM is unavailable."""
    if step.signal_added:
        signal_type = step.signal_added.type.replace("_", " ")
        return (
            f"A new {signal_type} signal was added at step {step.step_number}. "
            f"The algorithms have recalculated their recommendations. "
            f"Check the metrics chart to see how each one responded."
        )
    return (
        f"Step {step.step_number} processed. "
        f"The algorithms are working with the signals provided so far."
    )
