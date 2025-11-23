"""SSE streaming endpoint for narration.

GET /api/v1/simulation/{session_id}/narration/stream?step={step_number}

For template narrations: yields the full text in one event.
For LLM narrations: yields chunks as they stream from the Claude API.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from app.services.narration.llm_narrator import generate_narration
from app.services.session_manager import SessionManager

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["narration"])

# Module-level references (initialized during app startup)
_session_manager: SessionManager | None = None
_ground_truth_store: dict | None = None


def init_narration_router(
    session_manager: SessionManager,
    ground_truth_store: dict,
) -> None:
    """Called during app startup to inject dependencies."""
    global _session_manager, _ground_truth_store
    _session_manager = session_manager
    _ground_truth_store = ground_truth_store


async def _stream_narration(
    session_id: str,
    step_number: int,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Generate SSE events for a narration stream."""
    if _session_manager is None:
        raise RuntimeError("Session manager not initialized")

    # Look up session
    try:
        sid = UUID(session_id)
    except ValueError:
        yield ServerSentEvent(data="Invalid session ID", event="error")
        return

    state = _session_manager.get_session(sid)
    if state is None:
        yield ServerSentEvent(data="Session not found", event="error")
        return

    # Find the step
    step = None
    for s in state.steps:
        if s.step_number == step_number:
            step = s
            break

    if step is None:
        yield ServerSentEvent(data="Step not found", event="error")
        return

    # Check if narration is already a template (non-LLM)
    # If narration_source is "template", send the full text immediately
    if step.narration_source != "llm":
        yield ServerSentEvent(data=step.narration, event="chunk")
        yield ServerSentEvent(data="", event="done")
        return

    # Stream LLM narration
    previous_narrations = [s.narration for s in state.steps if s.step_number < step_number]
    full_text = ""

    async for chunk in generate_narration(state, step, previous_narrations):
        full_text += chunk
        yield ServerSentEvent(data=chunk, event="chunk")

    # Update the step's narration with the complete LLM text
    if full_text:
        step.narration = full_text

    yield ServerSentEvent(data="", event="done")


@router.get("/simulation/{session_id}/narration/stream")
async def stream_narration(
    session_id: str,
    step: int = Query(..., description="Step number to narrate"),
):
    """Stream narration for a specific simulation step via SSE.

    For template narrations, yields the full text in one event.
    For LLM narrations, yields chunks as they stream from the Claude API.
    Client detects completion via the 'done' event.
    """
    return EventSourceResponse(_stream_narration(session_id, step))
