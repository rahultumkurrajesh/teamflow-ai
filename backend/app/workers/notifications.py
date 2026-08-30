"""Notification job handlers.

These functions are called by the RQ worker when jobs are dequeued from Redis.
Each handler receives job parameters, creates a fresh DB session, and writes
the notification to the database.
"""
import uuid
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def handle_task_assigned(task_id: str, assignee_id: str) -> None:
    """Handle the task_assigned job.

    Creates a notification for the assigned user. Called by the RQ worker
    when the job is dequeued from Redis.

    Args:
        task_id: UUID of the task as string (serializable for Redis).
        assignee_id: UUID of the user being assigned as string.
    """
    # Defer imports to avoid circular dependencies and to ensure fresh
    # DB session for this worker process.
    from app.db.session import SessionLocal
    from app.repositories.notification import NotificationRepository
    from app.services.notification import NotificationService

    db: Session | None = None
    try:
        db = SessionLocal()
        repo = NotificationRepository(db)
        service = NotificationService(repo, db)
        service.create(
            message=f"You have been assigned to task {task_id}",
            user_id=uuid.UUID(assignee_id),
        )
        logger.info(
            f"Created task_assigned notification for user {assignee_id} on task {task_id}"
        )
    except Exception as e:
        logger.exception(f"Failed to create task_assigned notification: {e}")
        raise
    finally:
        if db:
            db.close()


def handle_comment_added(task_id: str, comment_id: str, task_assignee_id: str) -> None:
    """Handle the comment_added job.

    Creates a notification for the user assigned to the task. Called by the RQ
    worker when the job is dequeued from Redis.

    Args:
        task_id: UUID of the task as string.
        comment_id: UUID of the comment as string.
        task_assignee_id: UUID of the user assigned to the task as string.
    """
    from app.db.session import SessionLocal
    from app.repositories.notification import NotificationRepository
    from app.services.notification import NotificationService

    db: Session | None = None
    try:
        db = SessionLocal()
        repo = NotificationRepository(db)
        service = NotificationService(repo, db)
        service.create(
            message=f"A comment was added to task {task_id}",
            user_id=uuid.UUID(task_assignee_id),
        )
        logger.info(
            f"Created comment_added notification for user {task_assignee_id} on task {task_id}"
        )
    except Exception as e:
        logger.exception(f"Failed to create comment_added notification: {e}")
        raise
    finally:
        if db:
            db.close()
