import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash

from app.core.config import settings
from app.models.auth import AuthSession, User
from app.schemas.auth import TokenPair

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummy-password-for-timing")


def unauthorized() -> HTTPException:
    return HTTPException(
        401, "Negaliojantis arba pasibaigęs žetonas.", headers={"WWW-Authenticate": "Bearer"}
    )


def hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def is_expired(value: datetime) -> bool:
    # SQLite used in tests returns naive UTC timestamps.
    return value.replace(tzinfo=UTC) <= datetime.now(UTC)


def issue_tokens(user: User, session: AuthSession) -> TokenPair:
    now = datetime.now(UTC)
    refresh = secrets.token_urlsafe(48)
    session.refresh_hash = hash_refresh(refresh)
    access = jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role,
            "sid": session.id,
            "type": "access",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    return TokenPair(
        access_token=access, refresh_token=refresh, expires_in=settings.access_token_minutes * 60
    )


def decode_access(token: str) -> dict:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "role", "sid", "type", "jti", "iat", "exp", "iss", "aud"]},
        )
        if claims["type"] != "access" or not isinstance(claims["sid"], str):
            raise ValueError
        user_id = int(claims["sub"])
        if user_id < 1 or user_id > 2_147_483_647:
            raise ValueError
        return claims
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise unauthorized() from exc
