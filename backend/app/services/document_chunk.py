"""DocumentChunk service for embedding pipeline."""
import logging
import uuid

from sqlalchemy.orm import Session

from app.core.chunking import chunk_text
from app.core.embeddings import EmbeddingsClient
from app.core.storage import StorageClient
from app.core.text_extraction import extract_text
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk import DocumentChunkRepository

logger = logging.getLogger(__name__)


class DocumentChunkService:
    """Service for document chunking and embedding."""

    def __init__(
        self,
        db: Session,
        storage_client: StorageClient,
        embeddings_client: EmbeddingsClient,
    ):
        """Initialize service.

        Args:
            db: SQLAlchemy session.
            storage_client: Storage client for reading document bytes.
            embeddings_client: Embeddings client for generating vectors.
        """
        self.db = db
        self.storage = storage_client
        self.embeddings = embeddings_client
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
