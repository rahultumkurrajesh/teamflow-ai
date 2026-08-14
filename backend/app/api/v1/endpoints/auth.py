"""Authentication endpoints.

Thin, like the user endpoints: validate input, call the service, shape the
response. No password comparison, no token construction, no database access.
"""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair, status_code=status.HTTP_200_OK)
def login(
    data: LoginRequest, service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    """Exchange credentials for an access and refresh token pair."""
    return service.login(data.email, data.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    data: RefreshRequest, service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    """Exchange a valid refresh token for a new pair."""
    return service.refresh(data.refresh_token)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user. The frontend calls this on page load."""
    return UserRead.model_validate(user)
