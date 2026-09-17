import pytest
from tests.helpers import MockResult


class TestHealth:
    @pytest.mark.asyncio
    async def test_health(self, async_client):
        resp = await async_client.get("/api/mission/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "mission-service"


class TestGenerations:
    @pytest.mark.asyncio
    async def test_get_generations(self, async_client, mock_db, sample_generation, sample_generation_2):
        mock_db.execute.return_value = MockResult([sample_generation, sample_generation_2])
        resp = await async_client.get("/api/mission/generations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == "gen-1"
        assert data[0]["name"] == "Generation I"
        assert data[1]["id"] == "gen-2"

    @pytest.mark.asyncio
    async def test_get_generations_empty(self, async_client, mock_db):
        mock_db.execute.return_value = MockResult([])
        resp = await async_client.get("/api/mission/generations")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_generation_pokemon_found(self, async_client, mock_db, sample_generation, sample_pokemon):
        mock_db.get.return_value = sample_generation
        mock_db.execute.return_value = MockResult([sample_pokemon])
        resp = await async_client.get("/api/mission/generations/gen-1/pokemon")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Bulbasaur"

    @pytest.mark.asyncio
    async def test_get_generation_pokemon_not_found(self, async_client, mock_db):
        mock_db.get.return_value = None
        resp = await async_client.get("/api/mission/generations/gen-999/pokemon")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Generation not found"

    @pytest.mark.asyncio
    async def test_get_latest_generation_found(self, async_client, mock_db, sample_generation_2):
        mock_db.execute.return_value = MockResult([sample_generation_2])
        resp = await async_client.get("/api/mission/generations/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "gen-2"
        assert data["gen_number"] == 2

    @pytest.mark.asyncio
    async def test_get_latest_generation_empty(self, async_client, mock_db):
        mock_db.execute.return_value = MockResult([])
        resp = await async_client.get("/api/mission/generations/latest")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "No generations found"


class TestPokemon:
    @pytest.mark.asyncio
    async def test_get_pokemon(self, async_client, mock_db, sample_pokemon, sample_pokemon_2):
        mock_db.execute.return_value = MockResult([sample_pokemon, sample_pokemon_2])
        resp = await async_client.get("/api/mission/pokemon")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "Bulbasaur"
        assert data[1]["name"] == "Pikachu"

    @pytest.mark.asyncio
    async def test_get_one_pokemon_found(self, async_client, mock_db, sample_pokemon):
        mock_db.get.return_value = sample_pokemon
        resp = await async_client.get("/api/mission/pokemon/pk-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "pk-1"
        assert data["name"] == "Bulbasaur"
        assert data["type"] == "grass/poison"

    @pytest.mark.asyncio
    async def test_get_one_pokemon_not_found(self, async_client, mock_db):
        mock_db.get.return_value = None
        resp = await async_client.get("/api/mission/pokemon/pk-999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Pokémon not found"


class TestTypes:
    @pytest.mark.asyncio
    async def test_get_types(self, async_client, mock_db):
        # Query returns distinct type strings
        mock_db.execute.return_value = MockResult(["grass/poison", "electric"])
        resp = await async_client.get("/api/mission/types")
        assert resp.status_code == 200
        types = [t["name"] for t in resp.json()]
        assert "electric" in types
        assert "grass" in types
        assert "poison" in types

    @pytest.mark.asyncio
    async def test_get_types_empty(self, async_client, mock_db):
        mock_db.execute.return_value = MockResult([])
        resp = await async_client.get("/api/mission/types")
        assert resp.status_code == 200
        assert resp.json() == []
