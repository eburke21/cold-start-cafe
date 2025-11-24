import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.data.loader import DataStore
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers.challenge import evict_expired_challenges
from app.routers.challenge import router as challenge_router
from app.routers.movies import router as movies_router
from app.routers.narration import init_narration_router
from app.routers.narration import router as narration_router
from app.routers.simulation import get_ground_truth_store, init_simulation_router
from app.routers.simulation import router as simulation_router
from app.services.session_manager import SessionManager

logger = structlog.get_logger()


async def _session_cleanup_loop(
    session_manager: SessionManager,
    ttl_seconds: int,
    interval_seconds: int = 60,
) -> None:
    """Background task that evicts expired sessions every `interval_seconds`.

    Runs until cancelled (on app shutdown). Evicts both simulation sessions
    (via SessionManager) and challenge sessions (module-level dicts).
    """
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            sim_evicted = session_manager.evict_expired(ttl_seconds)
            challenge_evicted = evict_expired_challenges(ttl_seconds)
            if sim_evicted or challenge_evicted:
                logger.info(
                    "Session cleanup completed",
                    simulation_evicted=sim_evicted,
                    challenge_evicted=challenge_evicted,
                    ttl_seconds=ttl_seconds,
                )
        except Exception:
            logger.exception("Error during session cleanup")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup: load MovieLens data into memory
    logger.info("Starting ColdStart Café backend")
    data_store = DataStore(data_dir=settings.DATA_DIR)
    app.state.data = data_store
    logger.info(
        "Loaded %d movies, %d ratings, %d users",
        len(data_store.movies_df),
        len(data_store.ratings_df),
        len(data_store.users_df),
    )

    # Initialize session manager and inject into router
    session_manager = SessionManager(max_sessions=settings.MAX_CONCURRENT_SESSIONS)
    app.state.session_manager = session_manager
    init_simulation_router(session_manager)
    init_narration_router(session_manager, get_ground_truth_store())
    logger.info("Session manager initialized", max_sessions=settings.MAX_CONCURRENT_SESSIONS)

    # Start background session cleanup task
    cleanup_task = asyncio.create_task(
        _session_cleanup_loop(session_manager, settings.SIMULATION_TTL_SECONDS)
    )
    logger.info(
        "Session cleanup task started",
        ttl_seconds=settings.SIMULATION_TTL_SECONDS,
        interval_seconds=60,
    )

    yield

    # Shutdown: cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info(
        "Shutting down ColdStart Café backend",
        active_sessions=session_manager.session_count,
    )


app = FastAPI(
    title="ColdStart Café",
    description="Interactive cold-start problem simulator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (after CORS so preflight OPTIONS requests aren't limited)
app.add_middleware(RateLimitMiddleware)

# Register routers
app.include_router(simulation_router)
app.include_router(narration_router)
app.include_router(challenge_router)
app.include_router(movies_router)


# Global exception handler for ValueError → 400
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
