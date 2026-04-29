"""bcrypt + JWT round-trip tests."""

from __future__ import annotations

import pytest

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_access_token


def test_hash_and_verify_password_round_trip():
    plain = "correct horse battery staple!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_round_trip_returns_user_id():
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42


def test_jwt_invalid_token_rejected():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        decode_access_token("not-a-real-token")
    assert exc.value.status_code == 401
