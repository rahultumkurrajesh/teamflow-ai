"""User service.

This is where business rules live: no duplicate emails, passwords get hashed
before storage, and the transaction is committed here (the repository only
flushes). The service depends on the repository through its constructor, which
is the dependency injection the spec asks for and what makes the service unit
testable with a fake repository.
"""
import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def register(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise ConflictError("A user with this email already exists.")
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        self.repo.add(user)
        self.repo.db.commit()
        self.repo.db.refresh(user)
        return user

    def get(self, user_id: uuid.UUID) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    def list(self, limit: int = 50, offset: int = 0) -> list[User]:
        return self.repo.list(limit=limit, offset=offset)
