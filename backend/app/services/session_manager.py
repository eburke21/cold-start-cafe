"""In-memory session storage for simulation state.

Maps UUID → SimulationState. Thread-safe via threading.Lock.
Sessions are stored with creation timestamps for TTL-based cleanup
(actual cleanup logic deferred to Phase 7).
"""

import threading
import time
from uuid import UUID

from app.models.simulation import SimulationState


class SessionManager:
    """Thread-safe in-memory session store.

    Each simulation session gets a UUID key and a SimulationState value.
    The manager tracks creation timestamps for future TTL enforcement.
    """

    def __init__(self, max_sessions: int = 100) -> None:
        self._sessions: dict[UUID, SimulationState] = {}
        self._created_at: dict[UUID, float] = {}
        self._lock = threading.Lock()
        self._max_sessions = max_sessions

    def create_session(self) -> SimulationState:
        """Create a new simulation session with a fresh UUID.

        Returns:
            A new SimulationState with a unique session_id.

        Raises:
            RuntimeError: If max concurrent sessions exceeded.
        """
        with self._lock:
            if len(self._sessions) >= self._max_sessions:
                raise RuntimeError(
                    f"Max concurrent sessions ({self._max_sessions}) exceeded. "
                    "Try again later or close an existing session."
                )
            state = SimulationState()
            self._sessions[state.session_id] = state
            self._created_at[state.session_id] = time.time()
            return state

    def get_session(self, session_id: UUID) -> SimulationState | None:
        """Retrieve a session by ID. Returns None if not found."""
        with self._lock:
            return self._sessions.get(session_id)

    def delete_session(self, session_id: UUID) -> bool:
        """Delete a session. Returns True if it existed, False otherwise."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                del self._created_at[session_id]
                return True
            return False

    @property
    def session_count(self) -> int:
        """Number of active sessions."""
        with self._lock:
            return len(self._sessions)
