"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import INSECURE_SECRET_KEY, get_settings
from app.core.errors import register_exception_handlers
from app.database.database import engine
from app.routers import (
    achievements,
    ai,
    analytics,
    auth,
    emotions,
    habits,
    journal,
    users,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moodly")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Fail fast instead of signing tokens with a publicly known key.
    if settings.is_production and settings.secret_key == INSECURE_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY ist noch der Standardwert. Setze in der Produktion "
            "einen eigenen, zufälligen SECRET_KEY."
        )
    logger.info("Server started (environment=%s)", settings.environment)
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    description="Persönliche Journal-, Mood-, Habit- und Analytics-App",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(journal.router)
app.include_router(emotions.router)
app.include_router(habits.router)
app.include_router(analytics.router)
app.include_router(achievements.router)
app.include_router(ai.router)


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Health endpoint: verifies the API and the database connection."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        logger.exception("Database health check failed")
        database_status = "error"

    return {"status": "ok", "database": database_status}
