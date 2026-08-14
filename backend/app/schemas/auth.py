"""API schemas for authentication.

Passwords appear only on the way in, tokens only on the way out, following the
same input/output split as schemas/user.py. There is no schema here that could
carry a password hash, which keeps hashes out of responses by construction
rather than by remembering to strip them.

/auth/me deliberately reuses UserRead rather than defining another read model,
so the shape of a user is described in exactly one place.
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
