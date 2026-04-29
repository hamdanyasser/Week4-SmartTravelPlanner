"""Local backend smoke test for auth, tools, agent, and webhook fallback.

Run from `backend/` with:
    python -m app.smoke_test

The script avoids Postgres on purpose so reviewers can verify the backend
shape even when Docker/pgvector is not available.
"""

from __future__ import annotations

import asyncio
import os
import secrets

os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(32))
os.environ.setdefault("DISCORD_WEBHOOK_URL", "http://127.0.0.1:9/atlasbrief-smoke")
os.environ.setdefault("WEBHOOK_MAX_ATTEMPTS", "1")
os.environ.setdefault("WEBHOOK_TIMEOUT_SECONDS", "0.2")

from app.agent.graph import AtlasBriefAgent
from app.agent.registry import ALLOWED_TOOL_NAMES
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_access_token
from app.ml.service import load_travel_style_model
from app.webhooks.dispatcher import deliver_discord_webhook


async def main() -> None:
    """Run a short pass/fail smoke test."""

    assert {
        "retrieve_destination_knowledge",
        "classify_travel_style",
        "fetch_live_conditions",
    } == ALLOWED_TOOL_NAMES

    password_hash = hash_password("test-password")
    assert verify_password("test-password", password_hash)
    token = create_access_token(user_id=123)
    assert decode_access_token(token) == 123

    try:
        ml_model = load_travel_style_model()
    except Exception:
        ml_model = None

    agent = AtlasBriefAgent()
    state = await agent.run_state(
        query="Two weeks in July, $1,500, warm, hiking, not too touristy",
        session=None,
        ml_model=ml_model,
    )
    response = state["response"]
    tool_results = state.get("tool_results", [])

    assert response.top_pick.name == "Madeira"
    assert len(tool_results) == 3
    assert all(result.tool_name in ALLOWED_TOOL_NAMES for result in tool_results)
    assert response.tools_used

    webhook_result = await deliver_discord_webhook(response)
    assert webhook_result.status == "failed"

    print("Backend smoke test passed.")
    print(f"Top pick: {response.top_pick.name}, {response.top_pick.country}")
    print(f"Tools: {', '.join(result.tool_name for result in tool_results)}")
    print(f"Webhook failure isolated: {webhook_result.status}")


if __name__ == "__main__":
    asyncio.run(main())
