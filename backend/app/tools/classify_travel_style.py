"""Allowlisted ML tool: classify travel style."""

from __future__ import annotations

from typing import Any

from app.ml.service import classify_with_model, fallback_classification
from app.schemas.tools import ClassifyTravelStyleInput, ClassifyTravelStyleOutput

TOOL_NAME = "classify_travel_style"


async def classify_travel_style(
    payload: ClassifyTravelStyleInput | dict[str, Any],
    model: Any | None = None,
) -> ClassifyTravelStyleOutput:
    """Validate input and return the saved model's predicted travel style."""

    request = (
        payload
        if isinstance(payload, ClassifyTravelStyleInput)
        else ClassifyTravelStyleInput.model_validate(payload)
    )
    try:
        return classify_with_model(request, model=model)
    except Exception:
        return fallback_classification(request)
