"""DocumentChunk repository for database access."""
import uuid

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """Repository for DocumentChunk model."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy session.
        """
        self.db = db

    def add_batch(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Add multiple document chunks to the database.

        Args:
            chunks: List of DocumentChunk objects to add.

        Returns:
            List of added chunks (with IDs populated).
        """
        self.db.add_all(chunks)
        self.db.flush()
        return chunks

    def get_by_document_id(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        """Get all chunks for a document, ordered by chunk_index.

        Args:
            document_id: The document ID.

        Returns:
            List of DocumentChunk objects.
        """
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

    def delete_by_document_id(self, document_id: uuid.UUID) -> int:
        """Delete all chunks for a document.

        Args:
            document_id: The document ID.

        Returns:
            Number of chunks deleted.
        """
        result = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        return result
