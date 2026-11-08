"""Shared pytest fixtures for the backend test suite.

Tests run against an isolated in-memory SQLite database (never the real
``data/app.db`` file). ``DATABASE_URL`` must be set before ``apps.backend.database``
is imported anywhere, so this happens at module import time, before the ``client``
fixture (or any test module) imports ``apps.backend.main``.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient

from ..database import Base, engine
from apps.backend.main import app


@pytest.fixture()
def client():
    """A TestClient backed by a fresh, empty database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
