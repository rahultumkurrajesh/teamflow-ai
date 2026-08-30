"""Comment service.

Business rules: comments belong to a task which belongs to a project which
belongs to an organization. A user may only access comments in tasks in projects
in their own organization. Every create and delete is audited. The service owns
the transaction. Comments cannot be updated (append-only for now).

When a comment is created on a task with an assignee, a notification job is
enqueued. The API does not wait for the notification; the job is processed
asynchronously by a background worker.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionError
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.comment import CommentRepository
from app.schemas.comment import CommentCreate
from app.services.notification import NotificationService


class CommentService:
    def __init__(
        self, repo: CommentRepository, db: Session, notification_service: NotificationService
    ) -> None:
        self.repo = repo
        self.db = db
        self.notification_service = notification_service

    def create(
        self,
        current_user: User,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        data: CommentCreate,
    ) -> Comment:
        """Create a new comment on a task, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.db.get(Task, task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")

        comment = Comment(
            body=data.body,
            task_id=task_id,
            author_id=current_user.id,
        )
        self.repo.add(comment)

        # Audit log
        self.db.add(
            AuditLog(
                action="create",
                entity_type="comment",
                entity_id=str(comment.id),
                actor_id=current_user.id,
            )
        )

        self.db.commit()
        self.db.refresh(comment)

        # Enqueue notification if the task has an assignee
        if task.assignee_id:
            self.notification_service.enqueue_comment_added(task_id, comment.id, task.assignee_id)

        return comment

    def get(
        self,
        current_user: User,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        comment_id: uuid.UUID,
    ) -> Comment:
        """Get a comment by ID, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.db.get(Task, task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")

        comment = self.repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundError("Comment not found.")
        if comment.task_id != task_id:
            raise NotFoundError("Comment not found on this task.")
        return comment

    def list(
        self,
        current_user: User,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comment]:
        """List comments on a task, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.db.get(Task, task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")

        return self.repo.get_by_task(task_id, limit=limit, offset=offset)

    def delete(
        self,
        current_user: User,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        comment_id: uuid.UUID,
    ) -> None:
        """Delete a comment by ID, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.db.get(Task, task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")

        comment = self.repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundError("Comment not found.")
        if comment.task_id != task_id:
            raise NotFoundError("Comment not found on this task.")

        # Audit log before deletion
        self.db.add(
            AuditLog(
                action="delete",
                entity_type="comment",
                entity_id=str(comment.id),
                actor_id=current_user.id,
            )
        )

        self.repo.delete(comment)
        self.db.commit()

    @staticmethod
    def _check_organization_access(
        current_user: User, resource_organization_id: uuid.UUID
    ) -> None:
        """Raise PermissionError if the user is not in the resource's organization."""
        if current_user.organization_id != resource_organization_id:
            raise PermissionError("You do not have access to this resource.")
