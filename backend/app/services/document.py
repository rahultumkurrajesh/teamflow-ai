"""Document service.

Business rules: documents belong to a project which belongs to an organization.
A user may only access documents in projects in their own organization. Every
upload and delete is audited. The service owns the transaction; the repository
only flushes.

Files are stored in S3-compatible storage (MinIO locally, real S3 in production).
The service handles uploading to storage and writing metadata to the database.
"""
import uuid
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionError
from app.core.storage import storage
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User
from app.repositories.document import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, repo: DocumentRepository, db: Session) -> None:
        self.repo = repo
        self.db = db

    def upload(
        self,
        current_user: User,
        project_id: uuid.UUID,
        filename: str,
        file_content: bytes,
        content_type: str,
    ) -> Document:
        """Upload a file to a project.

        Stores the file in S3-compatible storage and saves metadata to the database.
        Enforces organization-scoped authorization.

        Args:
            current_user: The user uploading the file.
            project_id: UUID of the project.
            filename: Original filename.
            file_content: File contents as bytes.
            content_type: MIME type of the file.

        Returns:
            The created Document instance.

        Raises:
            NotFoundError if the project doesn't exist.
            PermissionError if the user doesn't belong to the project's organization.
        """
        # Verify project exists and user has access
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        # Generate storage key: project_id/document_id/filename
        document_id = uuid.uuid4()
        storage_key = f"{project_id}/{document_id}/{filename}"

        # Upload to S3-compatible storage
        try:
            storage.upload_file(storage_key, file_content, content_type)
            logger.info(f"Uploaded file to storage: {storage_key}")
        except Exception as e:
            logger.exception(f"Failed to upload file to storage: {e}")
            raise

        # Create document record
        document = Document(
            id=document_id,
            filename=filename,
            storage_key=storage_key,
            content_type=content_type,
            status=DocumentStatus.uploaded,
            project_id=project_id,
        )
        self.repo.add(document)

        # Audit log
        self.db.add(
            AuditLog(
                action="upload",
                entity_type="document",
                entity_id=str(document.id),
                actor_id=current_user.id,
            )
        )

        self.db.commit()
        self.db.refresh(document)
        return document

    def get(self, current_user: User, project_id: uuid.UUID, document_id: uuid.UUID) -> Document:
        """Get a document by ID, ensuring the user belongs to its project's organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        document = self.repo.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document not found.")
        if document.project_id != project_id:
            raise NotFoundError("Document not found in this project.")
        return document

    def list(
        self,
        current_user: User,
        project_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        """List documents for a project, ensuring the user belongs to its organization."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        return self.repo.get_by_project(project_id, limit=limit, offset=offset)

    def get_download_url(
        self, current_user: User, project_id: uuid.UUID, document_id: uuid.UUID
    ) -> tuple[str, int]:
        """Get a presigned URL for downloading a document.

        The URL is valid for 1 hour and can be used to download the file without
        authentication.

        Args:
            current_user: The user requesting the download URL.
            project_id: UUID of the project.
            document_id: UUID of the document.

        Returns:
            Tuple of (presigned_url, expiration_seconds).

        Raises:
            NotFoundError if the project or document doesn't exist.
            PermissionError if the user doesn't belong to the project's organization.
        """
        document = self.get(current_user, project_id, document_id)

        # Generate presigned URL
        try:
            url = storage.generate_presigned_url(document.storage_key, expiration=3600)
            logger.info(f"Generated presigned URL for document: {document_id}")
            return url, 3600
        except Exception as e:
            logger.exception(f"Failed to generate presigned URL: {e}")
            raise

    def delete(
        self, current_user: User, project_id: uuid.UUID, document_id: uuid.UUID
    ) -> None:
        """Delete a document and its file from storage.

        Args:
            current_user: The user deleting the document.
            project_id: UUID of the project.
            document_id: UUID of the document.

        Raises:
            NotFoundError if the project or document doesn't exist.
            PermissionError if the user doesn't belong to the project's organization.
        """
        document = self.get(current_user, project_id, document_id)

        # Delete from storage
        try:
            storage.delete_file(document.storage_key)
            logger.info(f"Deleted file from storage: {document.storage_key}")
        except Exception as e:
            logger.exception(f"Failed to delete file from storage: {e}")
            raise

        # Audit log before deletion
        self.db.add(
            AuditLog(
                action="delete",
                entity_type="document",
                entity_id=str(document.id),
                actor_id=current_user.id,
            )
        )

        self.repo.delete(document)
        self.db.commit()

    @staticmethod
    def _check_organization_access(
        current_user: User, resource_organization_id: uuid.UUID
    ) -> None:
        """Raise PermissionError if the user is not in the resource's organization."""
        if current_user.organization_id != resource_organization_id:
            raise PermissionError("You do not have access to this resource.")
