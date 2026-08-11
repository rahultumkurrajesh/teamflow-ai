"""Database engine, session factory, and the session dependency.

One SessionLocal per request. The get_db dependency yields a session and
guarantees it is closed even if the request raises. Transactions are committed
by the service layer, not here.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # drop dead connections instead of erroring mid-request
    echo=settings.debug,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
