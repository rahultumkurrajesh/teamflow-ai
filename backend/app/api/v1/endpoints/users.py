"""User endpoints.

Endpoints are thin: validate input (Pydantic does this automatically), call the
service, shape the response. No business logic, no database calls. Pagination is
done with limit/offset query params validated by FastAPI.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_user_service
from app.schemas.user import UserCreate, UserRead
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    data: UserCreate, service: UserService = Depends(get_user_service)
) -> UserRead:
    user = service.register(data)
    return UserRead.model_validate(user)


@router.get("", response_model=list[UserRead])
def list_users(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    users = service.list(limit=limit, offset=offset)
    return [UserRead.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: uuid.UUID, service: UserService = Depends(get_user_service)
) -> UserRead:
    return UserRead.model_validate(service.get(user_id))
