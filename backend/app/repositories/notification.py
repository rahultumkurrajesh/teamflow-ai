"""Notification repository.

The repository is the ONLY place that knows how notifications are stored.
It speaks SQLAlchemy and returns model instances. It never validates business
rules and never commits.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return self.db.get(Notification, notification_id)

    def get_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user, ordered by newest first."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_unread_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        """Get unread notifications for a user."""
        stmt = (
            select(Notification)
            .where((Notification.user_id == user_id) & (Notification.is_read.is_(False)))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification
