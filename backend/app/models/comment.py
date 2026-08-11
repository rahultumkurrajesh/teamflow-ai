"""Comment table.

Belongs to a task and has an author (a user). Deleting the task deletes its
comments; deleting the author keeps the comment but nulls the author link, so
history is preserved.
"""
import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task: Mapped["Task"] = relationship(back_populates="comments")  # noqa: F821

    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    author: Mapped["User | None"] = relationship()  # noqa: F821
