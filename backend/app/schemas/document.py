"""API schemas for documents.

Documents represent files uploaded to projects. The create schema is minimal
(just filename and file content via multipart), while the read schema includes
all metadata.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus


class DocumentCreate(BaseModel):
    """Input for file upload. The actual file content comes via multipart form."""
    pass  # File content is handled separately in the router via UploadFile


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    storage_key: str
    content_type: str
    status: DocumentStatus
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentDownloadResponse(BaseModel):
    """Response for download endpoint: presigned URL."""
    download_url: str
    expires_in: int = Field(description="URL expiration time in seconds")
