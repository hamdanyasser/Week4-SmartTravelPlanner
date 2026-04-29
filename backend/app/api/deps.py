"""FastAPI dependencies shared by routes."""

from __future__ import annotations

from contextlib import suppress
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.db.session import get_session
from app.models.user import User


async def _safe_rollback(session: AsyncSession) -> None:
    with suppress(Exception):
        await session.rollback()


async def _user_from_authorization(
    authorization: str | None,
    session: AsyncSession,
) -> User | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expected Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(token)
    try:
        user = await session.get(User, user_id)
    except Exception as exc:
        await _safe_rollback(session)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Require a valid JWT and return its user."""

    user = await _user_from_authorization(authorization, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Return a user when a token is present; allow anonymous otherwise."""

    return await _user_from_authorization(authorization, session)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Look up a user by normalized email."""

    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()
