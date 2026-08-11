"""User repository.

The repository is the ONLY place that knows how users are stored. It speaks
SQLAlchemy and returns model instances. It never validates business rules and
never commits. Swap PostgreSQL for something else and only this file changes.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, limit: int = 50, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()  # assign the PK without committing; service owns the commit
        return user
