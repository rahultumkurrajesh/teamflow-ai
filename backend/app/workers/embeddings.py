"""Background job handlers for document embedding."""
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.embeddings import get_embeddings_client
from app.core.storage import S3Storage
from app.services.document_chunk import DocumentChunkService

logger = logging.getLogger(__name__)
settings = get_settings()

# Create session factory for the worker (uses app's database)
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def handle_document_embedding(document_id: str) -> None:
    """Process a document for embedding.

    Opens its own DB session, extracts text, chunks it, generates embeddings,
    and stores DocumentChunk rows. Called as a background job from RQ.

    Args:
        document_id: Document ID as a string (RQ passes plain args).
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting embedding job for document {document_id}")

        # Create storage and embeddings clients
        storage = S3Storage()
        embeddings = get_embeddings_client()

        # Create service and process document
        service = DocumentChunkService(db, storage, embeddings)
        chunk_count = service.process_document(uuid.UUID(document_id))

        logger.info(f"Completed embedding job for document {document_id}: {chunk_count} chunks")

    except Exception as e:
        logger.error(
            f"Error in embedding job for document {document_id}: {e}",
            exc_info=True,
        )
        raise

    finally:
        db.close()
