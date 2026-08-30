"""Notification service.

This service handles both enqueueing notification jobs and creating
notifications. The enqueue methods are called from the API layer when events
occur (task assigned, comment added). The create method is called by workers
to actually write notifications to the database.

By separating enqueue from create, we keep the API responsive while ensuring
notifications are reliably written to the database.
"""
import uuid
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, repo: NotificationRepository, db: Session) -> None:
        self.repo = repo
        self.db = db

    def enqueue_task_assigned(self, task_id: uuid.UUID, assignee_id: uuid.UUID) -> None:
        """Enqueue a notification for a task assignment.

        Called from TaskService when a task is assigned or reassigned to a user.
        The job is processed asynchronously by the worker; this method returns
        immediately so the API is not blocked.

        Args:
            task_id: UUID of the task.
            assignee_id: UUID of the user being assigned.
        """
        # Import here to avoid circular dependency
        from app.core.queue import enqueue_job
        from app.workers.notifications import handle_task_assigned

        try:
            enqueue_job(handle_task_assigned, str(task_id), str(assignee_id))
            logger.debug(
                f"Enqueued task_assigned job for user {assignee_id} on task {task_id}"
            )
        except Exception as e:
            logger.exception(f"Failed to enqueue task_assigned notification: {e}")
            # Don't re-raise: notification failures should not break the API request

    def enqueue_comment_added(
        self, task_id: uuid.UUID, comment_id: uuid.UUID, task_assignee_id: uuid.UUID
    ) -> None:
        """Enqueue a notification for a comment addition.

        Called from CommentService when a comment is added to a task.
        The job is processed asynchronously by the worker.

        Args:
            task_id: UUID of the task.
            comment_id: UUID of the new comment.
            task_assignee_id: UUID of the user assigned to the task.
        """
        from app.core.queue import enqueue_job
        from app.workers.notifications import handle_comment_added

        if not task_assignee_id:
            # Only notify if someone is assigned to the task
            return

        try:
            enqueue_job(
                handle_comment_added,
                str(task_id),
                str(comment_id),
                str(task_assignee_id),
            )
            logger.debug(
                f"Enqueued comment_added job for user {task_assignee_id} on task {task_id}"
            )
        except Exception as e:
            logger.exception(f"Failed to enqueue comment_added notification: {e}")

    def create(self, message: str, user_id: uuid.UUID) -> Notification:
        """Create a new notification for a user.

        Called by workers to actually write notifications to the database.
        This method owns the transaction; the repository only flushes.

        Args:
            message: The notification message.
            user_id: UUID of the user to notify.

        Returns:
            The created Notification instance.
        """
        notification = Notification(
            message=message,
            is_read=False,
            user_id=user_id,
        )
        self.repo.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_as_read(self, notification_id: uuid.UUID) -> Notification:
        """Mark a notification as read.

        Args:
            notification_id: UUID of the notification.

        Returns:
            The updated Notification instance.

        Raises:
            NotFoundError if the notification doesn't exist.
        """
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification not found.")
        notification.is_read = True
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
