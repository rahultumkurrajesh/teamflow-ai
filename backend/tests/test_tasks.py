"""Tests for task service.

Tests verify that tasks are properly nested under projects and that
organization-scoped authorization is enforced.
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
from app.models.task import Task, TaskStatus  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task import TaskService
from app.services.notification import NotificationService
from app.repositories.notification import NotificationRepository


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
def other_project(other_org: Organization) -> Project:
    return Project(id=uuid.uuid4(), name="Other Project", organization_id=other_org.id)


# Create


def test_create_task(db: Session, org: Organization, user: User, project: Project) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskCreate(title="Test Task", description="A test task", status=TaskStatus.todo)

    task = service.create(user, project.id, data)

    assert task.title == "Test Task"
    assert task.description == "A test task"
    assert task.status == TaskStatus.todo
    assert task.project_id == project.id


def test_create_task_with_assignee(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    assignee_id = uuid.uuid4()
    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskCreate(title="Test Task", assignee_id=assignee_id)

    task = service.create(user, project.id, data)

    assert task.assignee_id == assignee_id


def test_create_task_project_not_found(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskCreate(title="Test Task")

    with pytest.raises(NotFoundError):
        service.create(user, uuid.uuid4(), data)


def test_create_task_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User, project: Project
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    db.add(project)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskCreate(title="Test Task")

    with pytest.raises(PermissionError):
        service.create(other_user, project.id, data)


# Read


def test_get_task(db: Session, org: Organization, user: User, project: Project) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    result = service.get(user, project.id, task.id)

    assert result.id == task.id
    assert result.title == "Test Task"


def test_get_task_not_found(db: Session, org: Organization, user: User, project: Project) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.get(user, project.id, uuid.uuid4())


def test_get_task_wrong_project(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.get(user, uuid.uuid4(), task.id)


def test_get_task_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User, project: Project
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    with pytest.raises(PermissionError):
        service.get(other_user, project.id, task.id)


def test_list_tasks(db: Session, org: Organization, user: User, project: Project) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    for i in range(3):
        task = Task(id=uuid.uuid4(), title=f"Task {i}", project_id=project.id)
        db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    tasks = service.list(user, project.id, limit=50, offset=0)

    assert len(tasks) == 3


# Update


def test_update_task(db: Session, org: Organization, user: User, project: Project) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Old Title", status=TaskStatus.todo, project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskUpdate(title="New Title", status=TaskStatus.in_progress)

    result = service.update(user, project.id, task.id, data)

    assert result.title == "New Title"
    assert result.status == TaskStatus.in_progress


def test_update_task_partial(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Original Title", status=TaskStatus.todo, project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskUpdate(title="New Title")

    result = service.update(user, project.id, task.id, data)

    assert result.title == "New Title"
    assert result.status == TaskStatus.todo


def test_update_task_not_found(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskUpdate(title="New Title")

    with pytest.raises(NotFoundError):
        service.update(user, project.id, uuid.uuid4(), data)


def test_update_task_wrong_project(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)
    data = TaskUpdate(title="New Title")

    with pytest.raises(NotFoundError):
        service.update(user, uuid.uuid4(), task.id, data)


# Delete


def test_delete_task(db: Session, org: Organization, user: User, project: Project) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)
    db.add(task)
    db.commit()
    task_id = task.id

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    service.delete(user, project.id, task_id)

    result = repo.get_by_id(task_id)
    assert result is None


def test_delete_task_not_found(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.delete(user, project.id, uuid.uuid4())


def test_delete_task_wrong_project(
    db: Session, org: Organization, user: User, project: Project
) -> None:
    db.add(org)
    db.add(user)
    db.add(project)
    task = Task(id=uuid.uuid4(), title="Test Task", project_id=project.id)
    db.add(task)
    db.commit()

    repo = TaskRepository(db)
    notif_repo = NotificationRepository(db)
    notif_service = NotificationService(notif_repo, db)
    service = TaskService(repo, db, notif_service)

    with pytest.raises(NotFoundError):
        service.delete(user, uuid.uuid4(), task.id)
