"""RAG (Retrieval Augmented Generation) endpoints for question-answering over documents."""
import logging
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_document_chunk_service
from app.models.user import User
from app.services.document_chunk import DocumentChunkService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["RAG"])


class AskRequest(BaseModel):
    """Request body for asking a question about project documents."""

    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class ChunkSource(BaseModel):
    """Source chunk metadata in RAG response."""

    chunk_id: str
    document_id: str
    chunk_index: int
    preview: str


class AskResponse(BaseModel):
    """Response from RAG question-answering endpoint."""

    answer: str
    chunks: list[ChunkSource]


@router.post(
    "/{project_id}/ask",
    response_model=AskResponse,
    summary="Ask a question about project documents (RAG)",
)
def ask_question(
    project_id: uuid.UUID,
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    service: DocumentChunkService = Depends(get_document_chunk_service),
) -> AskResponse:
    """Answer a question using RAG over documents in a project.

    Retrieves the most similar document chunks using vector search and
    generates a grounded answer using an LLM.

    Args:
        project_id: The project ID to search documents in.
        request: Question and optional top_k parameter.
        current_user: Authenticated user.
        service: DocumentChunkService for retrieval and answering.

    Returns:
        AskResponse with the answer and source chunks used.

    Raises:
        404 if project doesn't exist.
        403 if user doesn't belong to the project's organization.
    """
    result = service.answer_question(
        current_user,
        project_id,
        request.question,
        k=request.top_k,
    )

    return AskResponse(
        answer=result["answer"],
        chunks=[ChunkSource(**chunk) for chunk in result["chunks"]],
    )
