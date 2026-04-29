"""Runtime helpers for the saved travel-style model."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.schemas.tools import ClassifyTravelStyleInput, ClassifyTravelStyleOutput
from app.schemas.trip_brief import TravelStyle

ML_DIR = Path(__file__).resolve().parent
MODEL_PATH = ML_DIR / "model.joblib"

FEATURES = [
    "budget_level",
    "climate_warmth",
    "hiking_score",
    "culture_score",
    "tourism_level",
    "luxury_score",
    "family_score",
    "safety_score",
    "avg_daily_cost_usd",
]


@lru_cache(maxsize=1)
def load_travel_style_model() -> Any:
    """Load the joblib model once per process."""

    return joblib.load(MODEL_PATH)


def classify_with_model(
    payload: ClassifyTravelStyleInput,
    model: Any | None = None,
) -> ClassifyTravelStyleOutput:
    """Run the saved sklearn Pipeline and shape a Pydantic output."""

    model = model or load_travel_style_model()
    row = pd.DataFrame([{feature: getattr(payload, feature) for feature in FEATURES}])
    predicted = str(model.predict(row)[0])

    probabilities: dict[TravelStyle, float] = {}
    confidence = 1.0
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(row)[0]
        classes = [str(label) for label in model.classes_]
        probabilities = {
            TravelStyle(label): float(value)
            for label, value in zip(classes, proba, strict=False)
            if label in TravelStyle._value2member_map_
        }
        confidence = max(probabilities.values()) if probabilities else 1.0

    return ClassifyTravelStyleOutput(
        predicted_style=TravelStyle(predicted),
        confidence=confidence,
        probabilities=probabilities,
        used_fallback=False,
    )


def fallback_classification(payload: ClassifyTravelStyleInput) -> ClassifyTravelStyleOutput:
    """Safe deterministic fallback if the joblib model is unavailable."""

    if payload.hiking_score >= 4:
        style = TravelStyle.ADVENTURE
    elif payload.budget_level <= 2:
        style = TravelStyle.BUDGET
    elif payload.culture_score >= 4:
        style = TravelStyle.CULTURE
    else:
        style = TravelStyle.RELAXATION

    return ClassifyTravelStyleOutput(
        predicted_style=style,
        confidence=0.62,
        probabilities={style: 0.62},
        used_fallback=True,
        warning="Model unavailable; used rule-based fallback classification.",
    )
