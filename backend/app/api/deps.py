"""Dependency wiring for the API layer.

FastAPI resolves these at request time and injects them into endpoints. This is
the one place that knows how to assemble a service from a session, which keeps
that construction out of the endpoints themselves.

The auth dependencies live here too. get_current_user turns a bearer token into
a real user row, and require_role builds a dependency that enforces a minimum
role, so the authorisation rule sits in the route signature where a reviewer
can see it rather than buried inside a service.
"""
import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, PermissionError as AppPermissionError
from app.core.roles import at_least
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.user import UserService

# auto_error=False so a missing header raises our own AuthError and comes back
# in the project's {"error": {...}} envelope, rather than FastAPI's default
# {"detail": ...} shape.
_bearer = HTTPBearer(auto_error=False)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the bearer token to a user row.

    This costs one primary key lookup per request. That is the price of being
    able to revoke access immediately: a deactivated user is locked out on
    their next call rather than whenever their token happens to expire.
    """
    if credentials is None:
        raise AuthError("Missing bearer token.")

    payload = decode_token(credentials.credentials, expected_type="access")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError) as exc:
        raise AuthError("Could not validate credentials.") from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthError("User is no longer active.")
    return user


def require_role(required: UserRole) -> Callable[..., User]:
    """Build a dependency admitting only users at or above `required`.

    Used as: dependencies=[Depends(require_role(UserRole.admin))]
    """

    def _check(user: User = Depends(get_current_user)) -> User:
        if not at_least(user.role, required.value):
            raise AppPermissionError(
                f"This action requires the {required.value} role or higher."
            )
        return user

    return _check
