"""DocumentChunk repository for database access."""
import uuid

from sqlalchemy import Float
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.document import Document


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

    def get_similar_chunks(
        self,
        project_id: uuid.UUID,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[DocumentChunk]:
        """Retrieve the k most similar chunks for a project using vector similarity.

        Uses pgvector cosine distance (<=>) operator for efficient similarity search.
        Only returns chunks from documents in the specified project.

        Args:
            project_id: The project ID to scope the search to.
            query_embedding: The query embedding vector (e.g., from embedding the question).
            k: Number of top similar chunks to return (default 5).

        Returns:
            List of DocumentChunk objects ordered by similarity (most similar first).
        """
        # Use pgvector cosine distance operator (<=>)
        # The operator returns distance, so we order by distance ascending (smallest = most similar)
        cosine_distance = DocumentChunk.embedding.op("<=>", return_type=Float)(query_embedding)

        chunks = (
            self.db.query(DocumentChunk, cosine_distance.label("distance"))
            .join(Document)
            .filter(Document.project_id == project_id)
            .order_by("distance")
            .limit(k)
            .all()
        )

        # Extract just the DocumentChunk objects (discard the distance)
        return [chunk for chunk, _ in chunks]
