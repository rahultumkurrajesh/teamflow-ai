"""Document upload/download endpoints.

Handles file uploads to projects and downloads via presigned URLs.
Files are stored in S3-compatible storage (MinIO locally, S3 in production).
Every endpoint requires authentication and enforces organization-scoped access.
"""
import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.deps import get_current_user, get_document_service
from app.models.user import User
from app.schemas.document import DocumentDownloadResponse, DocumentRead
from app.services.document import DocumentService

router = APIRouter(tags=["documents"])


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    """Upload a file to a project.

    Args:
        project_id: UUID of the project.
        file: File to upload (multipart form data).
        current_user: Authenticated user (via bearer token).
        service: DocumentService instance.

    Returns:
        DocumentRead: Metadata of the uploaded document.
    """
    file_content = await file.read()
    document = service.upload(
        current_user,
        project_id,
        filename=file.filename or "unnamed",
        file_content=file_content,
        content_type=file.content_type or "application/octet-stream",
    )
    return DocumentRead.model_validate(document)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
def list_documents(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentRead]:
    """List documents for a project.

    Args:
        project_id: UUID of the project.
        limit: Maximum number of documents to return.
        offset: Number of documents to skip.
        current_user: Authenticated user.
        service: DocumentService instance.

    Returns:
        List of DocumentRead objects.
    """
    documents = service.list(current_user, project_id, limit=limit, offset=offset)
    return [DocumentRead.model_validate(d) for d in documents]


@router.get(
    "/projects/{project_id}/documents/{document_id}/download",
    response_model=DocumentDownloadResponse,
)
def get_download_url(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentDownloadResponse:
    """Get a presigned URL for downloading a document.

    The URL is valid for 1 hour and can be used to download the file without
    authentication.

    Args:
        project_id: UUID of the project.
        document_id: UUID of the document.
        current_user: Authenticated user.
        service: DocumentService instance.

    Returns:
        DocumentDownloadResponse with presigned URL and expiration time.
    """
    url, expires_in = service.get_download_url(current_user, project_id, document_id)
    return DocumentDownloadResponse(download_url=url, expires_in=expires_in)


@router.delete("/projects/{project_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete a document from a project.

    Args:
        project_id: UUID of the project.
        document_id: UUID of the document to delete.
        current_user: Authenticated user.
        service: DocumentService instance.
    """
    service.delete(current_user, project_id, document_id)
