from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


class TestFetchJson:
    @pytest.mark.asyncio
    async def test_fetch_json_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"results": [{"name": "bulbasaur"}]}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_client_class = MagicMock(return_value=mock_client)

        with patch("httpx.AsyncClient", mock_client_class):
            from app.poke_client import fetch_json
            result = await fetch_json("https://pokeapi.co/api/v2/pokemon?limit=10000&offset=0")
            assert result == {"results": [{"name": "bulbasaur"}]}

    @pytest.mark.asyncio
    async def test_fetch_json_failure(self):
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection error")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_client_class = MagicMock(return_value=mock_client)

        with patch("httpx.AsyncClient", mock_client_class):
            from app.poke_client import fetch_json
            result = await fetch_json("https://pokeapi.co/api/v2/bad-url")
            assert result == {}


class TestPokemonVals:
    def test_pokemon_vals_full(self):
        from app.poke_client import _pokemon_vals
        detail = {
            "name": "bulbasaur",
            "id": 1,
            "height": 7,
            "weight": 69,
            "types": [
                {"type": {"name": "grass"}},
                {"type": {"name": "poison"}},
            ],
            "abilities": [
                {"ability": {"name": "overgrow"}},
                {"ability": {"name": "chlorophyll"}},
            ],
            "base_experience": 64,
            "sprites": {
                "other": {
                    "official-artwork": {
                        "front_default": "https://example.com/1.png"
                    }
                }
            },
        }
        vals = _pokemon_vals(detail)
        assert vals["name"] == "Bulbasaur"
        assert vals["type"] == "grass/poison"
        assert vals["height_m"] == 0.7
        assert vals["mass_kg"] == 6.9
        assert vals["types_count"] == 2
        assert vals["abilities_count"] == 2
        assert vals["abilities"] == "overgrow, chlorophyll"
        assert vals["base_experience"] == 64
        assert vals["sprite_url"] == "https://example.com/1.png"

    def test_pokemon_vals_minimal(self):
        from app.poke_client import _pokemon_vals
        detail = {
            "name": "unknown",
            "id": 999,
            "types": [],
            "abilities": [],
            "sprites": {},
        }
        vals = _pokemon_vals(detail)
        assert vals["type"] == "normal"
        assert vals["height_m"] == 0
        assert vals["mass_kg"] == 0
        assert vals["abilities"] == "none"
        assert vals["base_experience"] == 50
        assert vals["sprite_url"] is None


class TestSyncPokemon:
    @pytest.mark.asyncio
    async def test_sync_pokemon_with_fallback(self):
        from app.poke_client import sync_pokemon, FALLBACK_POKEMON

        mock_db = AsyncMock()
        mock_db.get.return_value = None
        mock_db.execute.return_value = MagicMock()

        with patch("app.poke_client.fetch_json", return_value={"results": []}):
            count = await sync_pokemon(mock_db)
            assert count == len(FALLBACK_POKEMON)
            assert mock_db.add.call_count == len(FALLBACK_POKEMON)
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_sync_pokemon_with_api_data(self):
        from app.poke_client import sync_pokemon

        mock_db = AsyncMock()
        mock_db.get.return_value = None
        mock_db.execute.return_value = MagicMock()

        fake_results = {
            "results": [
                {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
                {"name": "charmander", "url": "https://pokeapi.co/api/v2/pokemon/4/"},
            ]
        }

        fake_detail_1 = {
            "name": "bulbasaur",
            "id": 1,
            "height": 7,
            "weight": 69,
            "types": [{"type": {"name": "grass"}}],
            "abilities": [{"ability": {"name": "overgrow"}}],
            "base_experience": 64,
            "sprites": {"other": {"official-artwork": {"front_default": "https://example.com/1.png"}}},
        }

        fake_detail_2 = {
            "name": "charmander",
            "id": 4,
            "height": 6,
            "weight": 85,
            "types": [{"type": {"name": "fire"}}],
            "abilities": [{"ability": {"name": "blaze"}}],
            "base_experience": 64,
            "sprites": {"other": {"official-artwork": {"front_default": "https://example.com/4.png"}}},
        }

        with patch("app.poke_client.fetch_json", side_effect=[fake_results, fake_detail_1, fake_detail_2]):
            count = await sync_pokemon(mock_db)
            assert count == 2

    @pytest.mark.asyncio
    async def test_sync_pokemon_updates_existing(self):
        from app.poke_client import sync_pokemon

        mock_db = AsyncMock()
        existing_pokemon = MagicMock()
        existing_pokemon.id = "pk-1"
        mock_db.get.return_value = existing_pokemon

        fake_results = {
            "results": [
                {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
            ]
        }
        fake_detail = {
            "name": "bulbasaur",
            "id": 1,
            "height": 7,
            "weight": 69,
            "types": [{"type": {"name": "grass"}}],
            "abilities": [{"ability": {"name": "overgrow"}}],
            "base_experience": 64,
            "sprites": {"other": {"official-artwork": {"front_default": "https://example.com/1.png"}}},
        }

        with patch("app.poke_client.fetch_json", side_effect=[fake_results, fake_detail]):
            count = await sync_pokemon(mock_db)
            assert count == 1
            assert mock_db.execute.called


class TestSyncGenerations:
    @pytest.mark.asyncio
    async def test_sync_generations_with_fallback(self):
        from app.poke_client import sync_generations, FALLBACK_GENERATIONS

        mock_db = AsyncMock()
        mock_db.get.return_value = None

        with patch("app.poke_client.fetch_json", return_value={"results": []}):
            count = await sync_generations(mock_db)
            assert count == len(FALLBACK_GENERATIONS)
            assert mock_db.add.call_count == len(FALLBACK_GENERATIONS)
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_sync_generations_updates_existing(self):
        from app.poke_client import sync_generations

        mock_db = AsyncMock()
        mock_db.get.return_value = MagicMock()
        mock_db.get.return_value.id = "gen-1"

        with patch("app.poke_client.fetch_json", return_value={"results": []}):
            count = await sync_generations(mock_db)
            assert count == 9
