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
from app.db.session import dispose_engine, get_session_factory
from app.logging_config import configure_logging, get_logger
from app.ml.service import load_travel_style_model
from app.rag.ingest_documents import seed_rag_if_empty
from app.tracing import configure_langsmith

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load process-level resources once, with deterministic fallbacks."""

    settings = get_settings()
    configure_logging(level="DEBUG" if settings.app_debug else "INFO")
    langsmith_active = configure_langsmith()
    log.info(
        "app.startup",
        extra={
            "env": settings.app_env,
            "debug": settings.app_debug,
            "langsmith": langsmith_active,
        },
    )

    app.state.agent = AtlasBriefAgent()
    app.state.ml_model = None
    app.state.startup_warnings = []

    try:
        app.state.ml_model = load_travel_style_model()
        log.info("ml_model.loaded")
    except Exception as exc:
        app.state.startup_warnings.append(
            f"ML model not loaded; classifier fallback active: {exc.__class__.__name__}"
        )
        log.warning(
            "ml_model.load_failed",
            extra={"exc_class": exc.__class__.__name__, "exc": str(exc)},
        )

    if settings.database_init_on_startup:
        try:
            await init_db()
            log.info("db.init_ok")
        except Exception as exc:
            app.state.startup_warnings.append(
                f"Database init skipped after failure: {exc.__class__.__name__}"
            )
            log.warning(
                "db.init_skipped",
                extra={"exc_class": exc.__class__.__name__, "exc": str(exc)},
            )

    if settings.rag_ingest_on_startup:
        try:
            session_factory = get_session_factory()
            async with session_factory() as session:
                ingest_stats = await seed_rag_if_empty(session=session)
            ingest_log = ingest_stats.model_dump(mode="json")
            ingest_log["rag_message"] = ingest_log.pop("message", None)
            log.info(
                "rag.seed_ok",
                extra=ingest_log,
            )
        except Exception as exc:
            app.state.startup_warnings.append(
                f"RAG startup ingest skipped after failure: {exc.__class__.__name__}"
            )
            log.warning(
                "rag.seed_skipped",
                extra={"exc_class": exc.__class__.__name__, "exc": str(exc)},
            )

    try:
        yield
    finally:
        await dispose_engine()
        log.info("app.shutdown")


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
