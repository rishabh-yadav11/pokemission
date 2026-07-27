import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from app.database import get_db
from app.main import app
from app.models import Generation, Pokemon
from tests.helpers import MockResult


@asynccontextmanager
async def noop_lifespan(_app):
    yield

app.router.lifespan_context = noop_lifespan


@pytest.fixture
def sample_generation():
    return Generation(
        id="gen-1",
        name="Generation I",
        gen_number=1,
        date_utc=datetime(1996, 2, 27, tzinfo=timezone.utc),
        complete=True,
        details="Region: Kanto. Games: Red, Blue. Pokémon discovered: 151.",
        region_name="Kanto",
        games="Red, Blue",
        total_species=151,
        pokemon_species=["bulbasaur", "charmander", "squirtle"],
    )


@pytest.fixture
def sample_generation_2():
    return Generation(
        id="gen-2",
        name="Generation II",
        gen_number=2,
        date_utc=datetime(1999, 11, 21, tzinfo=timezone.utc),
        complete=True,
        details="Region: Johto. Games: Gold, Silver. Pokémon discovered: 100.",
        region_name="Johto",
        games="Gold, Silver",
        total_species=100,
        pokemon_species=["chikorita", "cyndaquil", "totodile"],
    )


@pytest.fixture
def sample_pokemon():
    return Pokemon(
        id="pk-1",
        name="Bulbasaur",
        type="grass/poison",
        height_m=0.7,
        mass_kg=6.9,
        types_count=2,
        abilities_count=2,
        abilities="overgrow, chlorophyll",
        base_experience=64,
        description="A grass/poison type Pokémon",
        sprite_url="https://example.com/bulbasaur.png",
    )


@pytest.fixture
def sample_pokemon_2():
    return Pokemon(
        id="pk-25",
        name="Pikachu",
        type="electric",
        height_m=0.4,
        mass_kg=6.0,
        types_count=1,
        abilities_count=2,
        abilities="static, lightning-rod",
        base_experience=112,
        description="An electric type Pokémon",
        sprite_url="https://example.com/pikachu.png",
    )


@pytest_asyncio.fixture
def mock_db():
    mock = AsyncMock()
    mock.execute.return_value = MockResult([])
    mock.get.return_value = None
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
