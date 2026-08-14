"""Password hashing and JWT helpers.

Passwords are hashed with bcrypt via passlib and never stored or logged in
plain text. Tokens are HS256 JWTs signed with a secret that comes from the
environment, never the codebase.

Two token types are issued, and the type is recorded in a "typ" claim that is
checked on decode. Without that check a long-lived refresh token would be
accepted anywhere an access token is, which would hand out a durable
credential on every request.

  access   short lived, sent on every request, carries the role so an
           authorisation check needs no extra database read
  refresh  long lived, accepted only by /auth/refresh, deliberately carries
           no role
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AuthError

settings = get_settings()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]

# bcrypt hashes at most 72 bytes and newer builds raise rather than truncate
# silently, so the limit is applied here in one place.
_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    return _pwd.hash(plain[:_BCRYPT_MAX_BYTES])


def verify_password(plain: str, hashed: str) -> bool:
    """Check a password against a stored hash.

    Returns False instead of raising on a malformed hash, so one corrupted row
    cannot turn a failed login into a 500.
    """
    try:
        return _pwd.verify(plain[:_BCRYPT_MAX_BYTES], hashed)
    except ValueError:
        return False


def _encode(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str) -> str:
    """Mint a short lived access token carrying the user's role."""
    return _encode(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        {"role": str(role)},
    )


def create_refresh_token(subject: str) -> str:
    """Mint a long lived refresh token.

    No role is embedded on purpose. Roles change, and a demoted user must not
    keep old permissions until the refresh token expires. The role is re-read
    from the database on every refresh instead.
    """
    return _encode(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a token, or raise AuthError.

    Signature, expiry and token type are all checked here so no caller ever
    touches the jwt library directly.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise AuthError("Could not validate credentials.") from exc

    if payload.get("typ") != expected_type:
        raise AuthError("Wrong token type.")
    if not payload.get("sub"):
        raise AuthError("Could not validate credentials.")
    return payload
