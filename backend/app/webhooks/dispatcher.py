"""Discord webhook delivery with timeout, retry, and failure isolation."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.logging_config import get_logger
from app.models.webhook_delivery import WebhookDelivery
from app.schemas.trip_brief import TripBriefResponse

log = get_logger(__name__)


@dataclass(frozen=True)
class WebhookResult:
    status: str
    attempts: int
    response_status_code: int | None = None
    error: str | None = None


def _message_from_brief(brief: TripBriefResponse) -> str:
    return (
        f"AtlasBrief recommendation: {brief.top_pick.name}, "
        f"{brief.top_pick.country}\n"
        f"Verdict: {brief.final_verdict}"
    )


async def _store_delivery(
    session: AsyncSession | None,
    agent_run_id: int | None,
    result: WebhookResult,
) -> None:
    if session is None:
        return
    try:
        session.add(
            WebhookDelivery(
                agent_run_id=agent_run_id,
                channel="discord",
                status=result.status,
                attempts=result.attempts,
                response_status_code=result.response_status_code,
                error=result.error,
            )
        )
        await session.commit()
    except Exception:
        with suppress(Exception):
            await session.rollback()


async def deliver_discord_webhook(
    brief: TripBriefResponse,
    session: AsyncSession | None = None,
    agent_run_id: int | None = None,
) -> WebhookResult:
    """Deliver a brief to Discord; never raise to the user path."""

    settings = get_settings()
    if not settings.webhook_enabled or not settings.discord_webhook_url:
        result = WebhookResult(status="skipped", attempts=0, error="No Discord webhook configured.")
        await _store_delivery(session, agent_run_id, result)
        log.info("webhook.skipped", extra={"agent_run_id": agent_run_id, "reason": "not_configured"})
        return result

    attempts = 0
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(settings.webhook_max_attempts),
            wait=wait_exponential(multiplier=0.3, min=0.3, max=2),
            retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
            reraise=True,
        ):
            with attempt:
                attempts += 1
                async with httpx.AsyncClient(
                    timeout=settings.webhook_timeout_seconds
                ) as client:
                    response = await client.post(
                        settings.discord_webhook_url,
                        json={"content": _message_from_brief(brief)},
                    )
                    response.raise_for_status()
                    result = WebhookResult(
                        status="delivered",
                        attempts=attempts,
                        response_status_code=response.status_code,
                    )
                    await _store_delivery(session, agent_run_id, result)
                    log.info(
                        "webhook.delivered",
                        extra={
                            "agent_run_id": agent_run_id,
                            "attempts": attempts,
                            "status_code": response.status_code,
                        },
                    )
                    return result
    except Exception as exc:
        result = WebhookResult(
            status="failed",
            attempts=attempts,
            error=f"{exc.__class__.__name__}: {exc}",
        )
        await _store_delivery(session, agent_run_id, result)
        log.warning(
            "webhook.failed",
            extra={
                "agent_run_id": agent_run_id,
                "attempts": attempts,
                "exc_class": exc.__class__.__name__,
            },
        )
        return result

    result = WebhookResult(status="failed", attempts=attempts, error="Unknown webhook failure.")
    await _store_delivery(session, agent_run_id, result)
    return result
