"""Tests for document service and file upload.

Tests use a FakeStorageClient that stores files in memory, so no S3/MinIO is
needed for unit tests. Each test can verify that files are uploaded correctly,
metadata is saved, and organization-scoped authorization is enforced.
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import NotFoundError, PermissionError
from app.db.base import Base
# Import all models to ensure they're registered with SQLAlchemy's registry
from app.models.organization import Organization  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.document import Document, DocumentStatus  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentRead
from app.services.document import DocumentService


# In-memory SQLite for testing
@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# Fake storage that stores files in memory
class FakeStorageClient:
    """Mock storage client for testing."""

    def __init__(self):
        self.files = {}  # storage_key -> file_content

    def upload_file(
        self, storage_key: str, file_content: bytes, content_type: str = "application/octet-stream"
    ) -> None:
        self.files[storage_key] = file_content

    def download_file(self, storage_key: str) -> bytes:
        if storage_key not in self.files:
            raise FileNotFoundError(f"File not found: {storage_key}")
        return self.files[storage_key]

    def delete_file(self, storage_key: str) -> None:
        if storage_key in self.files:
            del self.files[storage_key]

    def generate_presigned_url(self, storage_key: str, expiration: int = 3600) -> str:
        if storage_key not in self.files:
            raise FileNotFoundError(f"File not found: {storage_key}")
        return f"https://example.com/download/{storage_key}?expires={expiration}"

    def file_exists(self, storage_key: str) -> bool:
        return storage_key in self.files


@pytest.fixture
def fake_storage():
    return FakeStorageClient()


@pytest.fixture
def org() -> Organization:
    return Organization(id=uuid.uuid4(), name="Test Org")


@pytest.fixture
def user(org: Organization) -> User:
    return User(
        id=uuid.uuid4(),
        email="rahul@example.com",
        full_name="Rahul Tumkur Rajesh",
        hashed_password="hashed_password",
        role=UserRole.member,
        is_active=True,
        organization_id=org.id,
    )


@pytest.fixture
def other_org() -> Organization:
    return Organization(id=uuid.uuid4(), name="Other Org")


@pytest.fixture
def other_user(other_org: Organization) -> User:
    return User(
        id=uuid.uuid4(),
        email="other@example.com",
        full_name="Other User",
        hashed_password="hashed_password",
        role=UserRole.member,
        is_active=True,
        organization_id=other_org.id,
    )


@pytest.fixture
def project(org: Organization) -> Project:
    return Project(id=uuid.uuid4(), name="Test Project", organization_id=org.id)


@pytest.fixture
def other_project(other_org: Organization) -> Project:
    return Project(id=uuid.uuid4(), name="Other Project", organization_id=other_org.id)


# Monkeypatch storage module to use fake storage
@pytest.fixture
def mock_storage(fake_storage, monkeypatch):
    """Replace app.core.storage.storage with fake storage for this test."""
    monkeypatch.setattr("app.services.document.storage", fake_storage)
    return fake_storage


# Tests


def test_upload_document(
    db: Session, org: Organization, user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)
    file_content = b"Test file content"

    document = service.upload(
        user,
        project.id,
        filename="test.txt",
        file_content=file_content,
        content_type="text/plain",
    )

    assert document.filename == "test.txt"
    assert document.content_type == "text/plain"
    assert document.status == DocumentStatus.uploaded
    assert document.project_id == project.id
    assert mock_storage.file_exists(document.storage_key)


def test_upload_document_without_organization(db: Session) -> None:
    user = User(
        id=uuid.uuid4(),
        email="noorg@example.com",
        full_name="No Org User",
        hashed_password="hashed_password",
        role=UserRole.member,
        is_active=True,
        organization_id=None,
    )
    project = Project(id=uuid.uuid4(), name="Test Project", organization_id=uuid.uuid4())
    db.add(user)
    db.add(project)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    with pytest.raises(PermissionError):
        service.upload(
            user, project.id, filename="test.txt", file_content=b"content", content_type="text/plain"
        )


def test_upload_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    db.add(project)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    with pytest.raises(PermissionError):
        service.upload(
            other_user, project.id, filename="test.txt", file_content=b"content", content_type="text/plain"
        )


def test_get_document(
    db: Session, org: Organization, user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    document = Document(
        id=uuid.uuid4(),
        filename="test.txt",
        storage_key="test-key",
        content_type="text/plain",
        status=DocumentStatus.uploaded,
        project_id=project.id,
    )
    db.add(document)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    result = service.get(user, project.id, document.id)

    assert result.id == document.id
    assert result.filename == "test.txt"


def test_get_document_not_found(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    with pytest.raises(NotFoundError):
        service.get(user, project.id, uuid.uuid4())


def test_list_documents(
    db: Session, org: Organization, user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    for i in range(3):
        document = Document(
            id=uuid.uuid4(),
            filename=f"file{i}.txt",
            storage_key=f"key{i}",
            content_type="text/plain",
            status=DocumentStatus.uploaded,
            project_id=project.id,
        )
        db.add(document)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    documents = service.list(user, project.id)

    assert len(documents) == 3


def test_get_download_url(
    db: Session, org: Organization, user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    document = Document(
        id=uuid.uuid4(),
        filename="test.txt",
        storage_key="test-key",
        content_type="text/plain",
        status=DocumentStatus.uploaded,
        project_id=project.id,
    )
    mock_storage.files["test-key"] = b"content"
    db.add(document)
    db.commit()

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    url, expires_in = service.get_download_url(user, project.id, document.id)

    assert "test-key" in url
    assert expires_in == 3600


def test_delete_document(
    db: Session, org: Organization, user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    document = Document(
        id=uuid.uuid4(),
        filename="test.txt",
        storage_key="test-key",
        content_type="text/plain",
        status=DocumentStatus.uploaded,
        project_id=project.id,
    )
    mock_storage.files["test-key"] = b"content"
    db.add(document)
    db.commit()
    document_id = document.id

    repo = DocumentRepository(db)
    service = DocumentService(repo, db)

    service.delete(user, project.id, document_id)

    result = repo.get_by_id(document_id)
    assert result is None
    assert not mock_storage.file_exists("test-key")


def test_document_read_schema(
    db: Session, org: Organization, user: User, project: Project, mock_storage
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    document = Document(
        id=uuid.uuid4(),
        filename="test.txt",
        storage_key="test-key",
        content_type="text/plain",
        status=DocumentStatus.uploaded,
        project_id=project.id,
    )
    db.add(document)
    db.commit()

    fetched = db.get(Document, document.id)
    schema = DocumentRead.model_validate(fetched)

    assert schema.filename == "test.txt"
    assert schema.content_type == "text/plain"
