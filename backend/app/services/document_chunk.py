"""DocumentChunk service for embedding pipeline and RAG retrieval."""
import logging
import uuid

from sqlalchemy.orm import Session

from app.core.chunking import chunk_text
from app.core.embeddings import EmbeddingsClient
from app.core.exceptions import NotFoundError, PermissionError as AppPermissionError
from app.core.llm import LLMClient
from app.core.storage import StorageClient
from app.core.text_extraction import extract_text
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.repositories.document_chunk import DocumentChunkRepository

logger = logging.getLogger(__name__)


class DocumentChunkService:
    """Service for document chunking and embedding."""

    def __init__(
        self,
        db: Session,
        storage_client: StorageClient,
        embeddings_client: EmbeddingsClient,
        llm_client: LLMClient | None = None,
    ):
        """Initialize service.

        Args:
            db: SQLAlchemy session.
            storage_client: Storage client for reading document bytes.
            embeddings_client: Embeddings client for generating vectors.
            llm_client: LLM client for RAG query-answer (optional, used only for answer_question).
        """
        self.db = db
        self.storage = storage_client
        self.embeddings = embeddings_client
        self.llm = llm_client
        self.repository = DocumentChunkRepository(db)

    def process_document(self, document_id: uuid.UUID) -> int:
        """Extract, chunk, embed, and store chunks for a document.

        The pipeline:
        1. Fetch document from DB
        2. Download file from storage
        3. Extract text based on content type
        4. Split into overlapping chunks
        5. Generate embeddings for each chunk
        6. Create and store DocumentChunk rows
        7. Commit transaction

        Args:
            document_id: The document ID to process.

        Returns:
            Number of chunks created.

        Raises:
            FileNotFoundError: If document not found.
            ValueError: If unsupported content type or extraction fails.
        """
        # Fetch document
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        if not document:
            raise FileNotFoundError(f"Document {document_id} not found")

        logger.info(f"Processing document {document_id}: {document.filename}")

        try:
            # Download file from storage
            file_bytes = self.storage.download_file(document.storage_key)

            # Extract text
            text = extract_text(file_bytes, document.content_type)
            logger.info(f"Extracted {len(text)} characters from {document.filename}")

            # Split into chunks
            chunk_texts = chunk_text(text)
            logger.info(f"Split into {len(chunk_texts)} chunks")

            # Generate embeddings and create rows
            embeddings = self.embeddings.embed_batch(chunk_texts)

            chunks_to_add = []
            for idx, (chunk_content, embedding) in enumerate(
                zip(chunk_texts, embeddings)
            ):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    content=chunk_content,
                    embedding=embedding,
                )
                chunks_to_add.append(chunk)

            # Store in database
            self.repository.add_batch(chunks_to_add)
            self.db.commit()

            logger.info(
                f"Successfully created {len(chunks_to_add)} chunks for document {document_id}"
            )
            return len(chunks_to_add)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error processing document {document_id}: {e}",
                exc_info=True,
            )
            raise

    def answer_question(
        self,
        current_user: User,
        project_id: uuid.UUID,
        question: str,
        k: int = 5,
    ) -> dict:
        """Answer a question using RAG over project documents.

        The pipeline:
        1. Verify user has access to the project's organization
        2. Embed the question
        3. Retrieve top-k similar chunks from the project
        4. Call the LLM with the question and retrieved context
        5. Return the answer and source chunk metadata

        Args:
            current_user: The user asking the question.
            project_id: UUID of the project to search.
            question: The question to answer.
            k: Number of top chunks to retrieve (default 5).

        Returns:
            Dictionary with keys:
            - answer: The LLM's grounded answer
            - chunks: List of dicts with chunk_id, chunk_index, document_id, similarity_snippet

        Raises:
            NotFoundError: If project doesn't exist.
            PermissionError: If user doesn't belong to project's organization.
        """
        if not self.llm:
            raise ValueError("LLM client not initialized; cannot answer questions")

        # Verify project exists and user has access
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project not found.")
        self._check_organization_access(current_user, project.organization_id)

        logger.info(
            f"Answering question for project {project_id} by user {current_user.id}"
        )

        try:
            # Embed the question
            question_embedding = self.embeddings.embed_text(question)

            # Retrieve similar chunks
            similar_chunks = self.repository.get_similar_chunks(
                project_id, question_embedding, k=k
            )

            if not similar_chunks:
                return {
                    "answer": "No relevant documents found in this project.",
                    "chunks": [],
                }

            # Extract chunk content for the LLM
            chunk_contents = [chunk.content for chunk in similar_chunks]

            # Call LLM to generate answer
            answer = self.llm.answer_question(question, chunk_contents)

            # Build source metadata
            sources = [
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "chunk_index": chunk.chunk_index,
                    "preview": chunk.content[:200] + "..."
                    if len(chunk.content) > 200
                    else chunk.content,
                }
                for chunk in similar_chunks
            ]

            logger.info(
                f"Answered question for project {project_id}: {len(similar_chunks)} chunks used"
            )
            return {"answer": answer, "chunks": sources}

        except Exception as e:
            logger.error(
                f"Error answering question for project {project_id}: {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def _check_organization_access(
        current_user: User, resource_organization_id: uuid.UUID
    ) -> None:
        """Raise PermissionError if the user is not in the resource's organization."""
        if current_user.organization_id != resource_organization_id:
            raise AppPermissionError("You do not have access to this resource.")
