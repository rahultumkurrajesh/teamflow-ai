"""Tests for project service.

The service tests pass a fake repository through the constructor, which is the
payoff of the dependency injection choice: none of these need Postgres, so they
run in milliseconds and need no service container in CI.
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import NotFoundError, PermissionError
from app.db.base import Base
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User, UserRole
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project import ProjectService


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


# Create


def test_create_project(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)
    data = ProjectCreate(name="Test Project", description="A test project")

    project = service.create(user, data)

    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.organization_id == org.id


def test_create_project_without_organization(db: Session) -> None:
    user = User(
        id=uuid.uuid4(),
        email="noorg@example.com",
        full_name="No Org User",
        hashed_password="hashed_password",
        role=UserRole.member,
        is_active=True,
        organization_id=None,
    )
    db.add(user)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)
    data = ProjectCreate(name="Test Project")

    with pytest.raises(PermissionError):
        service.create(user, data)


# Read


def test_get_project(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    project = Project(id=uuid.uuid4(), name="Test Project", organization_id=org.id)
    db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    result = service.get(user, project.id)

    assert result.id == project.id
    assert result.name == "Test Project"


def test_get_project_not_found(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    with pytest.raises(NotFoundError):
        service.get(user, uuid.uuid4())


def test_get_project_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    project = Project(id=uuid.uuid4(), name="Test Project", organization_id=org.id)
    db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    with pytest.raises(PermissionError):
        service.get(other_user, project.id)


def test_list_projects(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    for i in range(3):
        project = Project(
            id=uuid.uuid4(), name=f"Project {i}", organization_id=org.id
        )
        db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    projects = service.list(user, limit=50, offset=0)

    assert len(projects) == 3


def test_list_projects_empty_without_org(db: Session) -> None:
    user = User(
        id=uuid.uuid4(),
        email="noorg@example.com",
        full_name="No Org User",
        hashed_password="hashed_password",
        role=UserRole.member,
        is_active=True,
        organization_id=None,
    )
    db.add(user)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    projects = service.list(user)

    assert projects == []


# Update


def test_update_project(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    project = Project(id=uuid.uuid4(), name="Old Name", organization_id=org.id)
    db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)
    data = ProjectUpdate(name="New Name", description="New description")

    result = service.update(user, project.id, data)

    assert result.name == "New Name"
    assert result.description == "New description"


def test_update_project_partial(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    project = Project(
        id=uuid.uuid4(),
        name="Original Name",
        description="Original description",
        organization_id=org.id,
    )
    db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)
    data = ProjectUpdate(name="New Name")

    result = service.update(user, project.id, data)

    assert result.name == "New Name"
    assert result.description == "Original description"


def test_update_project_not_found(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)
    data = ProjectUpdate(name="New Name")

    with pytest.raises(NotFoundError):
        service.update(user, uuid.uuid4(), data)


def test_update_project_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    project = Project(id=uuid.uuid4(), name="Test Project", organization_id=org.id)
    db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)
    data = ProjectUpdate(name="New Name")

    with pytest.raises(PermissionError):
        service.update(other_user, project.id, data)


# Delete


def test_delete_project(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    project = Project(id=uuid.uuid4(), name="Test Project", organization_id=org.id)
    db.add(project)
    db.commit()
    project_id = project.id

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    service.delete(user, project_id)

    result = repo.get_by_id(project_id)
    assert result is None


def test_delete_project_not_found(db: Session, org: Organization, user: User) -> None:
    db.add(org)
    db.add(user)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    with pytest.raises(NotFoundError):
        service.delete(user, uuid.uuid4())


def test_delete_project_denied_by_org(
    db: Session, org: Organization, other_org: Organization, user: User, other_user: User
) -> None:
    db.add(org)
    db.add(other_org)
    db.add(user)
    db.add(other_user)
    project = Project(id=uuid.uuid4(), name="Test Project", organization_id=org.id)
    db.add(project)
    db.commit()

    repo = ProjectRepository(db)
    service = ProjectService(repo, db)

    with pytest.raises(PermissionError):
        service.delete(other_user, project.id)
