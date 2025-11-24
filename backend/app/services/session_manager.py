"""In-memory session storage for simulation state.

Maps UUID → SimulationState. Thread-safe via threading.Lock.
Sessions are stored with creation timestamps for TTL-based cleanup.
"""

import threading
import time
from uuid import UUID

import structlog

from app.models.simulation import SimulationState

logger = structlog.get_logger()


class SessionManager:
    """Thread-safe in-memory session store.

    Each simulation session gets a UUID key and a SimulationState value.
    The manager tracks creation timestamps for TTL-based eviction.
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

    def evict_expired(self, ttl_seconds: int) -> int:
        """Remove sessions older than the given TTL.

        Args:
            ttl_seconds: Maximum session age in seconds.

        Returns:
            Number of sessions evicted.
        """
        now = time.time()
        cutoff = now - ttl_seconds

        with self._lock:
            expired = [sid for sid, created in self._created_at.items() if created < cutoff]
            for sid in expired:
                del self._sessions[sid]
                del self._created_at[sid]

        if expired:
            logger.info(
                "Evicted expired sessions",
                count=len(expired),
                ttl_seconds=ttl_seconds,
                remaining=self.session_count,
            )

        return len(expired)

    @property
    def session_count(self) -> int:
        """Number of active sessions."""
        with self._lock:
            return len(self._sessions)
