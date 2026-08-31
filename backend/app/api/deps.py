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
from app.repositories.comment import CommentRepository
from app.repositories.document import DocumentRepository
from app.repositories.notification import NotificationRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.comment import CommentService
from app.services.document import DocumentService
from app.services.document_chunk import DocumentChunkService
from app.services.notification import NotificationService
from app.services.project import ProjectService
from app.services.task import TaskService
from app.services.user import UserService
from app.core.embeddings import get_embeddings_client
from app.core.llm import get_llm_client
from app.core.storage import storage

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


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(ProjectRepository(db), db)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    notification_service = get_notification_service(db)
    return TaskService(TaskRepository(db), db, notification_service)


def get_comment_service(db: Session = Depends(get_db)) -> CommentService:
    notification_service = get_notification_service(db)
    return CommentService(CommentRepository(db), db, notification_service)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db), db)


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(DocumentRepository(db), db)


def get_document_chunk_service(db: Session = Depends(get_db)) -> DocumentChunkService:
    embeddings_client = get_embeddings_client()
    llm_client = get_llm_client()
    return DocumentChunkService(db, storage, embeddings_client, llm_client)
