"""Project service.

Business rules: projects belong to an organization. A user may only access
projects in their own organization. Every create, update, delete is audited.
The service owns the transaction; the repository only flushes.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionError
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, repo: ProjectRepository, db: Session) -> None:
        self.repo = repo
        self.db = db

    def create(self, current_user: User, data: ProjectCreate) -> Project:
        """Create a new project in the current user's organization.

        Raises PermissionError if the user has no organization.
        """
        if not current_user.organization_id:
            raise PermissionError("You must belong to an organization to create projects.")

        project = Project(
            name=data.name,
            description=data.description,
            organization_id=current_user.organization_id,
        )
        self.repo.add(project)

        # Audit log
        self.db.add(
            AuditLog(
                action="create",
                entity_type="project",
                entity_id=str(project.id),
                actor_id=current_user.id,
            )
        )

        self.db.commit()
        self.db.refresh(project)
        return project

    def get(self, current_user: User, project_id: uuid.UUID) -> Project:
        """Get a project by ID, ensuring the user belongs to its organization."""
        project = self.repo.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)
        return project

    def list(
        self, current_user: User, limit: int = 50, offset: int = 0
    ) -> list[Project]:
        """List projects in the current user's organization."""
        if not current_user.organization_id:
            return []
        return self.repo.get_by_organization(
            current_user.organization_id, limit=limit, offset=offset
        )

    def update(
        self, current_user: User, project_id: uuid.UUID, data: ProjectUpdate
    ) -> Project:
        """Update a project by ID, ensuring the user belongs to its organization."""
        project = self.repo.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        # Update fields if provided
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description

        self.db.add(project)

        # Audit log
        self.db.add(
            AuditLog(
                action="update",
                entity_type="project",
                entity_id=str(project.id),
                actor_id=current_user.id,
            )
        )

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, current_user: User, project_id: uuid.UUID) -> None:
        """Delete a project by ID, ensuring the user belongs to its organization."""
        project = self.repo.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        # Audit log before deletion
        self.db.add(
            AuditLog(
                action="delete",
                entity_type="project",
                entity_id=str(project.id),
                actor_id=current_user.id,
            )
        )

        self.repo.delete(project)
        self.db.commit()

    @staticmethod
    def _check_organization_access(
        current_user: User, resource_organization_id: uuid.UUID
    ) -> None:
        """Raise PermissionError if the user is not in the resource's organization."""
        if current_user.organization_id != resource_organization_id:
            raise PermissionError(
                "You do not have access to this resource."
            )
