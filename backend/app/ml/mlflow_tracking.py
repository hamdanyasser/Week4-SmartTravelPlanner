"""Optional MLflow experiment tracking, layered on top of `results.csv`.

The brief makes MLflow an *optional* extra: results.csv stays the source
of truth that ships in the repo, and MLflow gives the same data a richer
home for anyone who wants to inspect runs in a dashboard.

This module is import-safe even when MLflow is not installed - all calls
are no-ops in that case. Activation requires both:

  - `mlflow` available (it is in `requirements-dev.txt`)
  - `MLFLOW_TRACKING_URI` env var set (e.g. `file:./mlruns` for local UI)

That gate keeps CI / Docker fast: production never spins up MLflow unless
a reviewer explicitly wants it.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

try:
    import mlflow as _mlflow
except ImportError:  # pragma: no cover - mlflow is dev-only
    _mlflow = None


def _enabled() -> bool:
    return _mlflow is not None and bool(os.environ.get("MLFLOW_TRACKING_URI"))


@contextmanager
def mlflow_run(experiment: str = "atlasbrief-classifier") -> Iterator[Any | None]:
    """Yield an MLflow run if tracking is configured, else a no-op."""

    if not _enabled():
        yield None
        return
    _mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    _mlflow.set_experiment(experiment)
    with _mlflow.start_run() as run:
        yield run


def log_params(params: dict[str, Any]) -> None:
    if not _enabled():
        return
    _mlflow.log_params(params)


def log_metrics(metrics: dict[str, float]) -> None:
    if not _enabled():
        return
    _mlflow.log_metrics(metrics)


def log_artifact(path: str | os.PathLike[str]) -> None:
    if not _enabled():
        return
    _mlflow.log_artifact(str(path))
