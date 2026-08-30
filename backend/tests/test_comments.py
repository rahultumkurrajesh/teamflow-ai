"""Tests for comment service.

Tests verify that comments are properly nested under tasks under projects and
that organization-scoped authorization is enforced.
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import NotFoundError, PermissionError
from app.db.base import Base
# Import all models to ensure they're registered with SQLAlchemy's registry
from app.models.comment import Comment  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.repositories.comment import CommentRepository
from app.repositories.notification import NotificationRepository
from app.schemas.comment import CommentCreate
from app.services.comment import CommentService
from app.services.notification import NotificationService


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
def task(project: Project) -> Task:
    return Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)


@pytest.fixture
def other_project(other_org: Organization) -> Project:
    return Project(id=uuid.uuid4(), name="Other Project", organization_id=other_org.id)


@pytest.fixture
def other_task(other_project: Project) -> Task:
    return Task(id=uuid.uuid4(), title="Other Task", project_id=other_project.id)


# Create


def test_create_comment(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)
    data = CommentCreate(body="Test comment")

    comment = service.create(user, project.id, task.id, data)

    assert comment.body == "Test comment"
    assert comment.task_id == task.id
    assert comment.author_id == user.id


def test_create_comment_project_not_found(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)
    data = CommentCreate(body="Test comment")

    with pytest.raises(NotFoundError):
        service.create(user, uuid.uuid4(), uuid.uuid4(), data)


def test_create_comment_task_not_found(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)
    data = CommentCreate(body="Test comment")

    with pytest.raises(NotFoundError):
        service.create(user, project.id, uuid.uuid4(), data)


def test_create_comment_task_wrong_project(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)
    data = CommentCreate(body="Test comment")

    with pytest.raises(NotFoundError):
        service.create(user, uuid.uuid4(), task.id, data)


def test_create_comment_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    db.add(project)
    db.add(task)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)
    data = CommentCreate(body="Test comment")

    with pytest.raises(PermissionError):
        service.create(other_user, project.id, task.id, data)


# Read


def test_get_comment(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    comment = Comment(id=uuid.uuid4(), body="Test comment", task_id=task.id, author_id=user.id)
    db.add(comment)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    result = service.get(user, project.id, task.id, comment.id)

    assert result.id == comment.id
    assert result.body == "Test comment"


def test_get_comment_not_found(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.get(user, project.id, task.id, uuid.uuid4())


def test_get_comment_wrong_task(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    comment = Comment(id=uuid.uuid4(), body="Test comment", task_id=task.id, author_id=user.id)
    db.add(comment)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.get(user, project.id, uuid.uuid4(), comment.id)


def test_get_comment_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    db.add(project)
    db.add(task)
    comment = Comment(id=uuid.uuid4(), body="Test comment", task_id=task.id, author_id=user.id)
    db.add(comment)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    with pytest.raises(PermissionError):
        service.get(other_user, project.id, task.id, comment.id)


def test_list_comments(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    for i in range(3):
        comment = Comment(
            id=uuid.uuid4(), body=f"Comment {i}", task_id=task.id, author_id=user.id
        )
        db.add(comment)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    comments = service.list(user, project.id, task.id, limit=50, offset=0)

    assert len(comments) == 3


# Delete


def test_delete_comment(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    comment = Comment(id=uuid.uuid4(), body="Test comment", task_id=task.id, author_id=user.id)
    db.add(comment)
    db.commit()
    comment_id = comment.id

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    service.delete(user, project.id, task.id, comment_id)

    result = repo.get_by_id(comment_id)
    assert result is None


def test_delete_comment_not_found(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.delete(user, project.id, task.id, uuid.uuid4())


def test_delete_comment_wrong_task(
    db: Session, org: Organization, user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.add(task)
    comment = Comment(id=uuid.uuid4(), body="Test comment", task_id=task.id, author_id=user.id)
    db.add(comment)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.delete(user, project.id, uuid.uuid4(), comment.id)


def test_delete_comment_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User, project: Project, task: Task
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    db.add(project)
    db.add(task)
    comment = Comment(id=uuid.uuid4(), body="Test comment", task_id=task.id, author_id=user.id)
    db.add(comment)
    db.commit()

    repo = CommentRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = CommentService(repo, db, notif_service)

    with pytest.raises(PermissionError):
        service.delete(other_user, project.id, task.id, comment.id)
