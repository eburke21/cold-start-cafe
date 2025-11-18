from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.data.loader import DataStore

logger = structlog.get_logger()


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
    yield
    # Shutdown
    logger.info("Shutting down ColdStart Café backend")


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


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
