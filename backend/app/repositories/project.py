"""Project repository.

The repository is the ONLY place that knows how projects are stored. It speaks
SQLAlchemy and returns model instances. It never validates business rules and
never commits. Swap PostgreSQL for something else and only this file changes.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def get_by_organization(
        self, organization_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()  # assign the PK without committing; service owns the commit
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.flush()
