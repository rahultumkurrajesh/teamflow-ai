"""Document repository.

The repository is the ONLY place that knows how documents are stored in the DB.
It speaks SQLAlchemy and returns model instances. It never validates business
rules and never commits.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def get_by_project(
        self, project_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Document]:
        """Get documents for a project, ordered by newest first."""
        stmt = (
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.flush()
