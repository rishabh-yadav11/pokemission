import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from app.database import get_db
from app.main import app
from app.models import Subscriber, Alert
from tests.helpers import MockResult


@asynccontextmanager
async def noop_lifespan(_app):
    yield

app.router.lifespan_context = noop_lifespan


@pytest.fixture
def sample_subscriber():
    sid = uuid4()
    return Subscriber(
        id=sid,
        name="Ash Ketchum",
        email="ash@pokemon.com",
        event_types=["generation", "rare"],
        confirmed=True,
    )


@pytest.fixture
def sample_alert(sample_subscriber):
    return Alert(
        id=uuid4(),
        subscriber_id=sample_subscriber.id,
        event_type="generation",
        message="New generation discovered: Generation X on 2024-01-01",
        link="/generations/gen-10",
        read=False,
    )


@pytest_asyncio.fixture
def mock_db():
    mock = AsyncMock()
    mock.execute.return_value = MockResult([])
    mock.get.return_value = None
    mock.refresh = AsyncMock()
    mock.add = MagicMock()
    mock.delete = AsyncMock()
    mock.commit = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def async_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
