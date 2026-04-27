"""FastAPI application entry point.

Kept intentionally small. Its only job is to:
  - build the FastAPI app
  - install middleware
  - register the lifespan handler (where future singletons will live:
    DB engine, ML model, embedding model, LLM client)
  - mount routers from `app.api.routes`

Anything more belongs in its own module.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, trip_briefs
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Process-level setup and teardown.

    Day 1: nothing to do here yet. From Day 5 we will create the DB
    engine, load the joblib ML model, and instantiate the LLM client
    here — exactly once per process — and expose them via Depends().
    """
    yield


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
    app.include_router(trip_briefs.router, prefix="/api/v1")

    return app


app = create_app()
