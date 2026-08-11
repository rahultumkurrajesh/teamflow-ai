"""Dependency wiring for the API layer.

FastAPI resolves these at request time and injects them into endpoints. This is
the one place that knows how to assemble a service from a session, which keeps
that construction out of the endpoints themselves.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user import UserRepository
from app.services.user import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))
