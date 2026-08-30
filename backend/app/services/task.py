"""Task service.

Business rules: tasks belong to a project which belongs to an organization.
A user may only access tasks in projects in their own organization. Every
create, update, delete is audited. The service owns the transaction.

When a task is assigned or reassigned, a notification job is enqueued to
notify the assignee. The API does not wait for the notification; the job
is processed asynchronously by a background worker.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionError
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.notification import NotificationService


class TaskService:
    def __init__(
        self, repo: TaskRepository, db: Session, notification_service: NotificationService
    ) -> None:
        self.repo = repo
        self.db = db
        self.notification_service = notification_service

    def create(
        self, current_user: User, project_id: uuid.UUID, data: TaskCreate
    ) -> Task:
        """Create a new task in a project, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = Task(
            title=data.title,
            description=data.description,
            status=data.status,
            project_id=project_id,
            assignee_id=data.assignee_id,
        )
        self.repo.add(task)

        # Audit log
        self.db.add(
            AuditLog(
                action="create",
                entity_type="task",
                entity_id=str(task.id),
                actor_id=current_user.id,
            )
        )

        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, current_user: User, project_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        """Get a task by ID, ensuring the user belongs to its project's organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")
        return task

    def list(
        self,
        current_user: User,
        project_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        """List tasks in a project, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        return self.repo.get_by_project(project_id, limit=limit, offset=offset)

    def update(
        self,
        current_user: User,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        data: TaskUpdate,
    ) -> Task:
        """Update a task by ID, ensuring the user belongs to its project's organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")

        # Track if assignee changed so we can enqueue a notification
        old_assignee_id = task.assignee_id
        new_assignee_id = data.assignee_id

        # Update fields if provided
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status
        if data.assignee_id is not None:
            task.assignee_id = data.assignee_id

        self.db.add(task)

        # Audit log
        self.db.add(
            AuditLog(
                action="update",
                entity_type="task",
                entity_id=str(task.id),
                actor_id=current_user.id,
            )
        )

        self.db.commit()
        self.db.refresh(task)

        # Enqueue notification if assignee changed
        if new_assignee_id is not None and new_assignee_id != old_assignee_id:
            self.notification_service.enqueue_task_assigned(task_id, new_assignee_id)

        return task

    def delete(
        self, current_user: User, project_id: uuid.UUID, task_id: uuid.UUID
    ) -> None:
        """Delete a task by ID, ensuring the user belongs to its project's organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found.")
        if task.project_id != project_id:
            raise NotFoundError("Task not found in this project.")

        # Audit log before deletion
        self.db.add(
            AuditLog(
                action="delete",
                entity_type="task",
                entity_id=str(task.id),
                actor_id=current_user.id,
            )
        )

        self.repo.delete(task)
        self.db.commit()

    @staticmethod
    def _check_organization_access(
        current_user: User, resource_organization_id: uuid.UUID
    ) -> None:
        """Raise PermissionError if the user is not in the resource's organization."""
        if current_user.organization_id != resource_organization_id:
            raise PermissionError("You do not have access to this resource.")
