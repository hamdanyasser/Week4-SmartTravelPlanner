"""Authentication routes."""

from __future__ import annotations

from contextlib import suppress

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_user_by_email
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.db.session import get_session
from app.logging_config import get_logger
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger(__name__)


def _read_user(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
    )


async def _safe_rollback(session: AsyncSession) -> None:
    with suppress(Exception):
        await session.rollback()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Create a user with a bcrypt-hashed password."""

    email = payload.email.strip().lower()
    try:
        existing = await get_user_by_email(session, email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with that email already exists.",
            )
        user = User(
            email=email,
            display_name=payload.display_name,
            password_hash=hash_password(payload.password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    except HTTPException:
        raise
    except Exception as exc:
        await _safe_rollback(session)
        log.warning(
            "auth.register_failed",
            extra={"exc_class": exc.__class__.__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
    log.info("auth.registered", extra={"user_id": user.id})
    return _read_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Verify a password and issue a JWT access token."""

    try:
        user = await get_user_by_email(session, payload.email.strip().lower())
    except Exception as exc:
        await _safe_rollback(session)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    if user is None or not verify_password(payload.password, user.password_hash):
        log.info(
            "auth.login_failed",
            extra={"reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    log.info("auth.login_ok", extra={"user_id": user.id})
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user."""

    return _read_user(user)
