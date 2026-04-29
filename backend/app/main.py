"""FastAPI application entry point.

This file stays intentionally small: create the app, install middleware,
register singleton resources in lifespan, and mount routers.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import AtlasBriefAgent
from app.api.routes import auth, health, trip_briefs
from app.config import get_settings
from app.db.init_db import init_db
from app.db.session import dispose_engine
from app.ml.service import load_travel_style_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load process-level resources once, with deterministic fallbacks."""

    settings = get_settings()
    app.state.agent = AtlasBriefAgent()
    app.state.ml_model = None
    app.state.startup_warnings = []

    try:
        app.state.ml_model = load_travel_style_model()
    except Exception as exc:
        app.state.startup_warnings.append(
            f"ML model not loaded; classifier fallback active: {exc.__class__.__name__}"
        )

    if settings.database_init_on_startup:
        try:
            await init_db()
        except Exception as exc:
            app.state.startup_warnings.append(
                f"Database init skipped after failure: {exc.__class__.__name__}"
            )

    try:
        yield
    finally:
        await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(trip_briefs.router, prefix="/api/v1")

    return app


app = create_app()
