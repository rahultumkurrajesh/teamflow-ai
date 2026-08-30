"""Tests for notification service and job enqueueing.

Tests use a FakeQueue that stores jobs in memory, so no Redis is needed
for unit tests. Each test can verify that jobs are enqueued correctly and
that the notification creation logic works as expected.
"""
import uuid
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
# Import all models to ensure they're registered with SQLAlchemy's registry
# before Base.metadata.create_all() is called
from app.models.organization import Organization  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationRead
from app.services.notification import NotificationService


# In-memory SQLite for testing
@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


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


# Fake queue for testing - stores jobs in memory instead of Redis


class FakeJob:
    """Mock RQ Job object."""

    def __init__(self, func: Any, args: tuple, kwargs: dict):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.id = str(uuid.uuid4())

    def __repr__(self) -> str:
        return f"<FakeJob id={self.id} func={self.func.__name__}>"


class FakeQueue:
    """Mock RQ Queue that stores jobs in memory."""

    def __init__(self) -> None:
        self.jobs: list[FakeJob] = []

    def enqueue(self, func: Any, *args: Any, **kwargs: Any) -> FakeJob:
        job = FakeJob(func, args, kwargs)
        self.jobs.append(job)
        return job

    def clear(self) -> None:
        self.jobs.clear()

    def get_jobs(self) -> list[FakeJob]:
        return self.jobs.copy()


@pytest.fixture
def fake_queue() -> FakeQueue:
    """Provide a fake queue for testing."""
    return FakeQueue()


# Monkey-patch enqueue_job to use fake queue for tests


@pytest.fixture
def mock_enqueue_job(fake_queue, monkeypatch):
    """Replace enqueue_job with fake queue for this test."""

    def fake_enqueue_job(func, *args, **kwargs):
        return fake_queue.enqueue(func, *args, **kwargs)

    # Patch at the source: app.core.queue.enqueue_job
    monkeypatch.setattr("app.core.queue.enqueue_job", fake_enqueue_job)
    return fake_queue


# Tests


def test_create_notification(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = NotificationRepository(db)
    service = NotificationService(repo, db)

    notification = service.create("You have a new notification", user.id)

    assert notification.message == "You have a new notification"
    assert notification.user_id == user.id
    assert notification.is_read is False


def test_get_by_user(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    for i in range(3):
        notification = Notification(
            id=uuid.uuid4(),
            message=f"Notification {i}",
            user_id=user.id,
            is_read=False,
        )
        db.add(notification)
    db.commit()

    repo = NotificationRepository(db)
    notifications = repo.get_by_user(user.id)

    assert len(notifications) == 3


def test_get_unread_by_user(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    for i in range(3):
        notification = Notification(
            id=uuid.uuid4(),
            message=f"Notification {i}",
            user_id=user.id,
            is_read=(i > 0),  # First is unread, rest are read
        )
        db.add(notification)
    db.commit()

    repo = NotificationRepository(db)
    unread = repo.get_unread_by_user(user.id)

    assert len(unread) == 1
    assert unread[0].is_read is False


def test_mark_as_read(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    notification = Notification(
        id=uuid.uuid4(),
        message="Test notification",
        user_id=user.id,
        is_read=False,
    )
    db.add(notification)
    db.commit()

    repo = NotificationRepository(db)
    service = NotificationService(repo, db)

    result = service.mark_as_read(notification.id)

    assert result.is_read is True


def test_enqueue_task_assigned(db: Session, org: Organization, user: User, mock_enqueue_job) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = NotificationRepository(db)
    service = NotificationService(repo, db)
    task_id = uuid.uuid4()

    service.enqueue_task_assigned(task_id, user.id)

    # Check that a job was enqueued
    jobs = mock_enqueue_job.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].func.__name__ == "handle_task_assigned"
    assert jobs[0].args == (str(task_id), str(user.id))


def test_enqueue_comment_added(db: Session, org: Organization, user: User, mock_enqueue_job) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = NotificationRepository(db)
    service = NotificationService(repo, db)
    task_id = uuid.uuid4()
    comment_id = uuid.uuid4()

    service.enqueue_comment_added(task_id, comment_id, user.id)

    # Check that a job was enqueued
    jobs = mock_enqueue_job.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].func.__name__ == "handle_comment_added"
    assert jobs[0].args == (str(task_id), str(comment_id), str(user.id))


def test_enqueue_comment_added_no_assignee(db: Session, mock_enqueue_job) -> None:
    """If task has no assignee, no notification should be enqueued."""
    repo = NotificationRepository(db)
    service = NotificationService(repo, db)
    task_id = uuid.uuid4()
    comment_id = uuid.uuid4()
    no_assignee = None

    service.enqueue_comment_added(task_id, comment_id, no_assignee)  # type: ignore

    # No job should be enqueued
    jobs = mock_enqueue_job.get_jobs()
    assert len(jobs) == 0


def test_notification_read_schema(db: Session, user: User) -> None:
    """Verify NotificationRead schema works with ORM model."""
    db.add(user)
    notification = Notification(
        id=uuid.uuid4(),
        message="Test",
        user_id=user.id,
        is_read=False,
    )
    db.add(notification)
    db.commit()

    # Re-fetch to get fresh instance with all attributes
    fetched = db.get(Notification, notification.id)
    schema = NotificationRead.model_validate(fetched)

    assert schema.message == "Test"
    assert schema.user_id == user.id
    assert schema.is_read is False
