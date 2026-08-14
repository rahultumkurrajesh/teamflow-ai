"""Authentication service.

Same shape as UserService: the repository arrives through the constructor, so a
unit test passes in a fake and never needs Postgres. This module raises domain
errors and never imports FastAPI, so it does not know what a status code is.

Nothing here writes to the database, so unlike UserService it never commits.
"""
import uuid

from app.core.exceptions import AuthError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.core.config import get_settings
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenPair

settings = get_settings()


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def login(self, email: str, password: str) -> TokenPair:
        """Exchange an email and password for a token pair.

        The failure message is identical whether the email is unknown or the
        password is wrong. Distinguishing them would let anyone enumerate which
        addresses have accounts.
        """
        user = self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthError("Incorrect email or password.")
        if not user.is_active:
            raise AuthError("This account is disabled.")
        return self._issue(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        """Trade a valid refresh token for a fresh pair.

        The user is re-read here deliberately, so that someone deactivated or
        demoted since the refresh token was issued cannot mint a new access
        token carrying their old role.
        """
        payload = decode_token(refresh_token, expected_type="refresh")
        try:
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, TypeError) as exc:
            raise AuthError("Could not validate credentials.") from exc

        user = self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthError("User is no longer active.")
        return self._issue(user)

    @staticmethod
    def _issue(user: User) -> TokenPair:
        role = user.role.value if hasattr(user.role, "value") else str(user.role)
        return TokenPair(
            access_token=create_access_token(str(user.id), role),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=settings.access_token_expire_minutes * 60,
        )
