from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data_pipeline.config.settings import settings
from data_pipeline.storage.models import Base


def make_engine(database_url: str | None = None):
    return create_engine(database_url or settings.database_url, future=True)


def make_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def create_all(engine) -> None:
    """Convenience for tests (SQLite). Production schema is managed by Alembic
    (see migrations/versions/0001_initial_schema.py) — this is never called
    against the production database."""
    Base.metadata.create_all(engine)
