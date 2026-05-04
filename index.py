"""Vercel FastAPI entrypoint.

The application code lives under `backend/app`, where local Docker and tests
run it directly as `app.main:app`. Vercel imports this root `index.py`, so we
add `backend/` to `sys.path` and then expose the same FastAPI instance.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
