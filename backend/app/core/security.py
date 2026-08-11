"""Password hashing and JWT helpers.

Passwords are hashed with bcrypt and never stored or logged in plain text.
Tokens are short-lived HS256 JWTs signed with a secret from the environment.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(plain: str) -> str:
    # bcrypt operates on bytes and has a hard 72-byte input limit.
    pw = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pw, hashed.encode("utf-8"))