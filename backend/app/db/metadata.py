"""Import every model here so that anything importing `Base` also registers all
tables on `Base.metadata`. Alembic's autogenerate and the app both rely on this
being the single place that knows the full set of models.
"""
from app.db.base import Base  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "AuditLog",
    "Comment",
    "Document",
    "Notification",
    "Organization",
    "Project",
    "Task",
    "User",
]
