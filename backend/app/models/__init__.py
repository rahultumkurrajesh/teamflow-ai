"""SQLAlchemy models for the application.

All models must be imported here to ensure they are registered in the SQLAlchemy
registry before relationships are resolved.
"""
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.document_chunk import DocumentChunk  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401
