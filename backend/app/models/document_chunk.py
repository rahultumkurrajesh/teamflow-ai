"""Document chunk table for RAG (Retrieval Augmented Generation).

Chunks are pieces of a document split for semantic search. Each chunk stores
the text content and its embedding vector. The embedding enables similarity
search for retrieval augmented generation.

The embedding dimension is configurable via settings (default 1536 for OpenAI
text-embedding-3-small), and the pgvector extension handles efficient vector
similarity search via HNSW or IVFFLAT indexes.
"""
import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.document import Document

settings = get_settings()


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    # Indexes for vector similarity search and document lookup
    __table_args__ = (
        Index("idx_document_chunks_document_id", "document_id"),
        Index(
            "idx_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 200},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Vector embedding: dimension configured via settings (default 1536 for OpenAI)
    embedding: Mapped[Vector] = mapped_column(
        Vector(dim=settings.embedding_dimension), nullable=True
    )

    # Relationship to document (for convenience)
    document: Mapped["Document"] = relationship(back_populates="chunks")  # noqa: F821
