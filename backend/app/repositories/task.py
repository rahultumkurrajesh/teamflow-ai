"""Task repository.

The repository is the ONLY place that knows how tasks are stored. It speaks
SQLAlchemy and returns model instances. It never validates business rules and
never commits.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        return self.db.get(Task, task_id)

    def get_by_project(
        self, project_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_project_and_status(
        self,
        project_id: uuid.UUID,
        status: TaskStatus,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        stmt = (
            select(Task)
            .where((Task.project_id == project_id) & (Task.status == status))
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()
