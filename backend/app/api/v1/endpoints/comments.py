"""Comment endpoints.

Comments are nested under tasks under projects:
/projects/{project_id}/tasks/{task_id}/comments. Every endpoint requires
authentication and enforces organization-scoped access.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_comment_service
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.services.comment import CommentService

router = APIRouter(tags=["comments"])


@router.post(
    "/projects/{project_id}/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    comment = service.create(current_user, project_id, task_id, data)
    return CommentRead.model_validate(comment)


@router.get(
    "/projects/{project_id}/tasks/{task_id}/comments", response_model=list[CommentRead]
)
def list_comments(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> list[CommentRead]:
    comments = service.list(current_user, project_id, task_id, limit=limit, offset=offset)
    return [CommentRead.model_validate(c) for c in comments]


@router.get(
    "/projects/{project_id}/tasks/{task_id}/comments/{comment_id}",
    response_model=CommentRead,
)
def get_comment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    comment = service.get(current_user, project_id, task_id, comment_id)
    return CommentRead.model_validate(comment)


@router.delete(
    "/projects/{project_id}/tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> None:
    service.delete(current_user, project_id, task_id, comment_id)
