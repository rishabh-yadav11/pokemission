from datetime import datetime, timezone


class TestGenerationModel:
    def test_generation_creation(self):
        from app.models import Generation
        gen = Generation(
            id="gen-1",
            name="Generation I",
            gen_number=1,
            date_utc=datetime(1996, 2, 27, tzinfo=timezone.utc),
            complete=True,
            details="First generation",
            region_name="Kanto",
            games="Red, Blue",
            total_species=151,
            pokemon_species=["bulbasaur", "charmander"],
        )
        assert gen.id == "gen-1"
        assert gen.name == "Generation I"
        assert gen.gen_number == 1
        assert gen.total_species == 151
        assert gen.pokemon_species == ["bulbasaur", "charmander"]

    def test_generation_defaults(self):
        from app.models import Generation
        gen = Generation(id="gen-9", name="Generation IX")
        assert gen.id == "gen-9"
        assert gen.gen_number is None
        assert gen.complete is None
        assert gen.pokemon_species is None

    def test_generation_tablename(self):
        from app.models import Generation
        assert Generation.__tablename__ == "generations"


class TestPokemonModel:
    def test_pokemon_creation(self):
        from app.models import Pokemon
        p = Pokemon(
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
        assert p.id == "pk-25"
        assert p.name == "Pikachu"
        assert p.type == "electric"
        assert p.height_m == 0.4
        assert p.abilities == "static, lightning-rod"

    def test_pokemon_defaults(self):
        from app.models import Pokemon
        p = Pokemon(id="pk-1", name="Bulbasaur")
        assert p.type is None
        assert p.base_experience is None

    def test_pokemon_tablename(self):
        from app.models import Pokemon
        assert Pokemon.__tablename__ == "pokemon"
