"""Pydantic schema validation: valid and invalid payloads.

The brief calls this out as a required test type. Pydantic is our fence at
external boundaries; if a schema accepts garbage, the agent is exposed.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.rag import DestinationKnowledgeQuery
from app.schemas.tools import (
    ClassifyTravelStyleInput,
    FetchLiveConditionsInput,
)
from app.schemas.trip_brief import TravelStyle, TripBriefRequest


class TestTripBriefRequest:
    def test_valid(self):
        req = TripBriefRequest(query="I want two weeks in July with a $1500 budget")
        assert req.query.startswith("I want")

    def test_too_short_query_rejected(self):
        with pytest.raises(ValidationError):
            TripBriefRequest(query="hi")

    def test_too_long_query_rejected(self):
        with pytest.raises(ValidationError):
            TripBriefRequest(query="x" * 2001)


class TestClassifyTravelStyleInput:
    def test_valid_with_defaults(self):
        req = ClassifyTravelStyleInput(query="Two weeks of warm island hiking")
        assert req.budget_level == 3
        assert req.hiking_score == 5

    @pytest.mark.parametrize(
        "field,value",
        [
            ("budget_level", 0),
            ("budget_level", 6),
            ("hiking_score", -1),
            ("avg_daily_cost_usd", 5),
            ("avg_daily_cost_usd", 5000),
        ],
    )
    def test_out_of_range_rejected(self, field, value):
        with pytest.raises(ValidationError):
            ClassifyTravelStyleInput(query="ok query", **{field: value})


class TestFetchLiveConditionsInput:
    def test_valid(self):
        req = FetchLiveConditionsInput(
            query="warm hiking trip", destination="Madeira", country="Portugal", trip_month="July"
        )
        assert req.destination == "Madeira"

    def test_missing_destination_rejected(self):
        with pytest.raises(ValidationError):
            FetchLiveConditionsInput(query="ok query")  # type: ignore[call-arg]

    def test_destination_too_short_rejected(self):
        with pytest.raises(ValidationError):
            FetchLiveConditionsInput(query="ok query", destination="X")


class TestDestinationKnowledgeQuery:
    def test_valid(self):
        q = DestinationKnowledgeQuery(query="Madeira hiking")
        assert q.top_k == 5

    def test_top_k_capped(self):
        with pytest.raises(ValidationError):
            DestinationKnowledgeQuery(query="hiking", top_k=11)

    def test_destination_filter_optional(self):
        q = DestinationKnowledgeQuery(query="alpine", destinations=["Slovenia"])
        assert q.destinations == ["Slovenia"]


class TestAuthSchemas:
    def test_register_valid(self):
        r = RegisterRequest(email="user@example.com", password="hunter22!")
        assert r.email == "user@example.com"

    def test_register_short_password_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="short")

    def test_login_valid(self):
        r = LoginRequest(email="user@example.com", password="anything")
        assert r.password == "anything"


class TestTravelStyleEnum:
    def test_six_labels_locked(self):
        assert {s.value for s in TravelStyle} == {
            "Adventure",
            "Relaxation",
            "Culture",
            "Budget",
            "Luxury",
            "Family",
        }
