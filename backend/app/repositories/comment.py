"""Comment repository.

The repository is the ONLY place that knows how comments are stored. It speaks
SQLAlchemy and returns model instances. It never validates business rules and
never commits.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        return self.db.get(Comment, comment_id)

    def get_by_task(
        self, task_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add(self, comment: Comment) -> Comment:
        self.db.add(comment)
        self.db.flush()
        return comment

    def delete(self, comment: Comment) -> None:
        self.db.delete(comment)
        self.db.flush()
