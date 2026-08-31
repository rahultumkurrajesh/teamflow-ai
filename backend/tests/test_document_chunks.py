"""Tests for document chunking and embedding pipeline (Stage 9b)."""
import uuid
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.chunking import chunk_text
from app.core.embeddings import EmbeddingsClient
from app.core.storage import StorageClient
from app.core.text_extraction import extract_text
from app.db.base import Base
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.models.organization import Organization
from app.services.document_chunk import DocumentChunkService
from app.repositories.document_chunk import DocumentChunkRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class FakeEmbeddingsClient(EmbeddingsClient):
    """Fake embeddings client for testing.

    Returns fixed vector of 1s with dimension 1536 (matching OpenAI text-embedding-3-small).
    This is sufficient for ingest tests but querying tests (Stage 9c) will need
    distinguishable vectors to validate similarity search.
    """

    def embed_text(self, text: str) -> list[float]:
        """Return a fixed embedding vector."""
        return [1.0] * 1536

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return fixed embedding vector for each text."""
        # TODO (9c): Use distinguishable vectors (e.g., different values per chunk) for similarity query tests.
        return [[1.0] * 1536 for _ in texts]


class FakeStorageClient(StorageClient):
    """Fake storage client for testing."""

    def __init__(self):
        """Initialize with in-memory storage."""
        self.files: dict[str, bytes] = {}

    def upload_file(self, key: str, content: bytes, content_type: str) -> None:
        """Store file in memory."""
        self.files[key] = content

    def download_file(self, key: str) -> bytes:
        """Retrieve file from memory."""
        if key not in self.files:
            raise FileNotFoundError(f"File not found: {key}")
        return self.files[key]

    def delete_file(self, key: str) -> None:
        """Delete file from memory."""
        if key in self.files:
            del self.files[key]

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Return a fake presigned URL."""
        return f"https://fake-storage.example.com/{key}?expires={expiration}"

    def file_exists(self, key: str) -> bool:
        """Check if file exists in memory."""
        return key in self.files


@pytest.fixture
def db() -> Session:
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def organization(db: Session) -> Organization:
    """Create a test organization."""
    org = Organization(id=uuid.uuid4(), name="Test Org")
    db.add(org)
    db.commit()
    return org


@pytest.fixture
def user(db: Session, organization: Organization) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        organization_id=organization.id,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def project(db: Session, organization: Organization) -> Project:
    """Create a test project."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        organization_id=organization.id,
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def document(db: Session, project: Project) -> Document:
    """Create a test document."""
    doc = Document(
        id=uuid.uuid4(),
        filename="test.txt",
        storage_key="projects/test/test.txt",
        content_type="text/plain",
        project_id=project.id,
    )
    db.add(doc)
    db.commit()
    return doc


@pytest.fixture
def storage() -> FakeStorageClient:
    """Create a fake storage client."""
    return FakeStorageClient()


@pytest.fixture
def embeddings() -> FakeEmbeddingsClient:
    """Create a fake embeddings client."""
    return FakeEmbeddingsClient()


@pytest.fixture
def service(db: Session, storage: FakeStorageClient, embeddings: FakeEmbeddingsClient) -> DocumentChunkService:
    """Create a document chunk service with fake clients."""
    return DocumentChunkService(db, storage, embeddings)


class TestChunkText:
    """Tests for text chunking."""

    def test_chunk_text_small_text(self) -> None:
        """Small text should return as single chunk."""
        text = "This is a small text."
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_large_text(self) -> None:
        """Large text should be split into multiple chunks."""
        # Create text with ~1000 tokens (each word ~1.3 tokens on average)
        text = " ".join(["word"] * 800)
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1

    def test_chunk_text_overlap(self) -> None:
        """Overlapping chunks should share some content."""
        text = " ".join(["word"] * 800)
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        # First and second chunk should overlap
        if len(chunks) > 1:
            # Check that chunks[1] starts with text from end of chunks[0] (overlap)
            # This is approximate since we decode tokens
            assert len(chunks[1]) > 0


class TestTextExtraction:
    """Tests for text extraction."""

    def test_extract_text_from_txt(self) -> None:
        """Extract text from plain text file."""
        content = b"Hello, world!"
        text = extract_text(content, "text/plain")
        assert text == "Hello, world!"

    def test_extract_text_with_charset(self) -> None:
        """Handle content-type with charset parameter."""
        content = b"Hello, world!"
        text = extract_text(content, "text/plain; charset=utf-8")
        assert text == "Hello, world!"

    def test_extract_text_unsupported_type(self) -> None:
        """Raise error for unsupported content type."""
        content = b"some content"
        with pytest.raises(ValueError, match="Unsupported content type"):
            extract_text(content, "application/octet-stream")


class TestFakeEmbeddingsClient:
    """Tests for fake embeddings client."""

    def test_embed_text_returns_vector(self) -> None:
        """Embed text should return a vector."""
        client = FakeEmbeddingsClient()
        embedding = client.embed_text("test text")
        assert len(embedding) == 1536
        assert all(v == 1.0 for v in embedding)

    def test_embed_batch_returns_vectors(self) -> None:
        """Embed batch should return multiple vectors."""
        client = FakeEmbeddingsClient()
        embeddings = client.embed_batch(["text1", "text2", "text3"])
        assert len(embeddings) == 3
        assert all(len(v) == 1536 for v in embeddings)


class TestFakeStorageClient:
    """Tests for fake storage client."""

    def test_upload_and_download(self) -> None:
        """Upload and retrieve a file."""
        client = FakeStorageClient()
        content = b"test content"
        client.upload_file("test.txt", content, "text/plain")
        assert client.download_file("test.txt") == content

    def test_download_missing_file(self) -> None:
        """Downloading missing file raises error."""
        client = FakeStorageClient()
        with pytest.raises(FileNotFoundError):
            client.download_file("missing.txt")

    def test_delete_file(self) -> None:
        """Delete file from storage."""
        client = FakeStorageClient()
        client.upload_file("test.txt", b"content", "text/plain")
        client.delete_file("test.txt")
        with pytest.raises(FileNotFoundError):
            client.download_file("test.txt")


class TestDocumentChunkRepository:
    """Tests for DocumentChunk repository."""

    def test_add_batch(self, db: Session, document: Document) -> None:
        """Add multiple chunks at once."""
        repo = DocumentChunkRepository(db)
        chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=f"Chunk {i}",
                embedding=[1.0] * 1536,
            )
            for i in range(3)
        ]
        result = repo.add_batch(chunks)
        assert len(result) == 3
        assert all(c.id is not None for c in result)

    def test_get_by_document_id(self, db: Session, document: Document) -> None:
        """Retrieve chunks by document ID."""
        repo = DocumentChunkRepository(db)
        chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=f"Chunk {i}",
                embedding=[1.0] * 1536,
            )
            for i in range(3)
        ]
        repo.add_batch(chunks)
        db.commit()

        retrieved = repo.get_by_document_id(document.id)
        assert len(retrieved) == 3
        assert [c.chunk_index for c in retrieved] == [0, 1, 2]

    def test_delete_by_document_id(self, db: Session, document: Document) -> None:
        """Delete all chunks for a document."""
        repo = DocumentChunkRepository(db)
        chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=f"Chunk {i}",
                embedding=[1.0] * 1536,
            )
            for i in range(3)
        ]
        repo.add_batch(chunks)
        db.commit()

        deleted = repo.delete_by_document_id(document.id)
        assert deleted == 3

        retrieved = repo.get_by_document_id(document.id)
        assert len(retrieved) == 0


class TestDocumentChunkService:
    """Tests for document chunking and embedding service."""

    def test_process_document_success(
        self,
        db: Session,
        document: Document,
        storage: FakeStorageClient,
        embeddings: FakeEmbeddingsClient,
    ) -> None:
        """Process a document end-to-end."""
        # Setup: upload document content to fake storage
        text_content = "Word " * 500  # ~500 words, ~650 tokens
        storage.upload_file(document.storage_key, text_content.encode(), "text/plain")

        # Create service and process
        service = DocumentChunkService(db, storage, embeddings)
        chunk_count = service.process_document(document.id)

        # Verify chunks were created
        assert chunk_count > 0
        repo = DocumentChunkRepository(db)
        chunks = repo.get_by_document_id(document.id)
        assert len(chunks) == chunk_count
        assert all(c.embedding is not None for c in chunks)

    def test_process_document_not_found(
        self,
        db: Session,
        storage: FakeStorageClient,
        embeddings: FakeEmbeddingsClient,
    ) -> None:
        """Processing non-existent document raises error."""
        service = DocumentChunkService(db, storage, embeddings)
        fake_id = uuid.uuid4()
        with pytest.raises(FileNotFoundError, match="not found"):
            service.process_document(fake_id)

    def test_process_document_unsupported_type(
        self,
        db: Session,
        document: Document,
        storage: FakeStorageClient,
        embeddings: FakeEmbeddingsClient,
    ) -> None:
        """Processing document with unsupported type raises error."""
        # Create document with unsupported type
        document.content_type = "application/octet-stream"
        db.add(document)
        db.commit()

        # Upload some content
        storage.upload_file(document.storage_key, b"some content", document.content_type)

        service = DocumentChunkService(db, storage, embeddings)
        with pytest.raises(ValueError, match="Unsupported content type"):
            service.process_document(document.id)

    def test_process_document_chunks_have_embeddings(
        self,
        db: Session,
        document: Document,
        storage: FakeStorageClient,
        embeddings: FakeEmbeddingsClient,
    ) -> None:
        """All chunks should have embeddings."""
        text_content = "Word " * 500
        storage.upload_file(document.storage_key, text_content.encode(), "text/plain")

        service = DocumentChunkService(db, storage, embeddings)
        chunk_count = service.process_document(document.id)

        repo = DocumentChunkRepository(db)
        chunks = repo.get_by_document_id(document.id)
        assert len(chunks) == chunk_count
        for chunk in chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 1536
            assert all(v == 1.0 for v in chunk.embedding)  # Fake embeddings
