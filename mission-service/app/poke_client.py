import asyncio
import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models import Generation, Pokemon

POKEAPI_BASE = "https://pokeapi.co/api/v2"

FALLBACK_POKEMON = [
    {"name":"bulbasaur","id":1,"height":7,"weight":69,"types":[{"type":{"name":"grass"}},{"type":{"name":"poison"}}],"abilities":[{"ability":{"name":"overgrow"}},{"ability":{"name":"chlorophyll"}}],"sprites":{"other":{"official-artwork":{"front_default":"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png"}}}},
    {"name":"charmander","id":4,"height":6,"weight":85,"types":[{"type":{"name":"fire"}}],"abilities":[{"ability":{"name":"blaze"}},{"ability":{"name":"solar-power"}}],"sprites":{"other":{"official-artwork":{"front_default":"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/4.png"}}}},
    {"name":"squirtle","id":7,"height":5,"weight":90,"types":[{"type":{"name":"water"}}],"abilities":[{"ability":{"name":"torrent"}},{"ability":{"name":"rain-dish"}}],"sprites":{"other":{"official-artwork":{"front_default":"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/7.png"}}}},
    {"name":"pikachu","id":25,"height":4,"weight":60,"types":[{"type":{"name":"electric"}}],"abilities":[{"ability":{"name":"static"}},{"ability":{"name":"lightning-rod"}}],"sprites":{"other":{"official-artwork":{"front_default":"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png"}}}},
    {"name":"mewtwo","id":150,"height":20,"weight":1220,"types":[{"type":{"name":"psychic"}}],"abilities":[{"ability":{"name":"pressure"}},{"ability":{"name":"unnerve"}}],"sprites":{"other":{"official-artwork":{"front_default":"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/150.png"}}}},
]

FALLBACK_GENERATIONS = [
    {"name":"generation-i","id":1,"main_region":{"name":"kanto"},"version_groups":[{"name":"red-blue"},{"name":"yellow"}]},
    {"name":"generation-ii","id":2,"main_region":{"name":"johto"},"version_groups":[{"name":"gold-silver"},{"name":"crystal"}]},
    {"name":"generation-iii","id":3,"main_region":{"name":"hoenn"},"version_groups":[{"name":"ruby-sapphire"},{"name":"emerald"},{"name":"firered-leafgreen"}]},
    {"name":"generation-iv","id":4,"main_region":{"name":"sinnoh"},"version_groups":[{"name":"diamond-pearl"},{"name":"platinum"},{"name":"heartgold-soulsilver"}]},
    {"name":"generation-v","id":5,"main_region":{"name":"unova"},"version_groups":[{"name":"black-white"},{"name":"black-2-white-2"}]},
    {"name":"generation-vi","id":6,"main_region":{"name":"kalos"},"version_groups":[{"name":"x-y"},{"name":"omega-ruby-alpha-sapphire"}]},
    {"name":"generation-vii","id":7,"main_region":{"name":"alola"},"version_groups":[{"name":"sun-moon"},{"name":"ultra-sun-ultra-moon"},{"name":"lets-go-pikachu-lets-go-eevee"}]},
    {"name":"generation-viii","id":8,"main_region":{"name":"galar"},"version_groups":[{"name":"sword-shield"},{"name":"brilliant-diamond-shining-pearl"},{"name":"legends-arceus"}]},
    {"name":"generation-ix","id":9,"main_region":{"name":"paldea"},"version_groups":[{"name":"scarlet-violet"},{"name":"the-teal-mask"},{"name":"the-indigo-disk"}]},
]


async def fetch_json(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"PokéAPI request to {url} failed ({e})")
        return {}


BATCH_SIZE = 50


def _pokemon_vals(detail: dict) -> dict:
    types_str = "/".join(t["type"]["name"] for t in detail.get("types", []))
    abilities_list = [a["ability"]["name"] for a in detail.get("abilities", [])]
    sprite = detail.get("sprites", {}).get("other", {}).get("official-artwork", {}).get("front_default")
    if not sprite:
        sprite = detail.get("sprites", {}).get("front_default")
    return {
        "name": detail["name"].title(),
        "type": types_str or "normal",
        "height_m": detail["height"] / 10.0 if detail.get("height") else 0,
        "mass_kg": detail["weight"] / 10.0 if detail.get("weight") else 0,
        "types_count": len(detail.get("types", [])),
        "abilities_count": len(detail.get("abilities", [])),
        "abilities": ", ".join(abilities_list) if abilities_list else "none",
        "base_experience": detail.get("base_experience", 50),
        "description": f"#{detail['id']} - {types_str.title() if types_str else 'Unknown'} type Pokémon. Abilities: {', '.join(abilities_list)}.",
        "sprite_url": sprite,
        "cached_at": datetime.now(timezone.utc),
    }


async def sync_pokemon(db: AsyncSession):
    list_data = await fetch_json(f"{POKEAPI_BASE}/pokemon?limit=10000&offset=0")
    results = list_data.get("results", [])
    if not results:
        results = FALLBACK_POKEMON
        print("Using fallback Pokémon data")
    sem = asyncio.Semaphore(10)

    async def fetch_detail(url):
        async with sem:
            return await fetch_json(url)

    count = 0
    for i in range(0, len(results), BATCH_SIZE):
        batch = results[i:i + BATCH_SIZE]
        details = await asyncio.gather(*[
            fetch_detail(e["url"]) for e in batch if isinstance(e, dict) and "url" in e
        ])
        for e in batch:
            if isinstance(e, dict) and "url" not in e:
                details.append(e)
        for detail in details:
            if not detail or not detail.get("name"):
                continue
            pid = f"pk-{detail['id']}"
            existing = await db.get(Pokemon, pid)
            vals = _pokemon_vals(detail)
            if existing:
                await db.execute(update(Pokemon).where(Pokemon.id == pid).values(**vals))
            else:
                db.add(Pokemon(id=pid, **vals))
            count += 1
        await db.commit()
        print(f"  Synced {count}/{len(results)} Pokémon...")

    print(f"Synced {count} Pokémon")
    return count


async def sync_generations(db: AsyncSession):
    data = await fetch_json(f"{POKEAPI_BASE}/generation")
    gens = data.get("results", []) or FALLBACK_GENERATIONS
    count = 0

    for i, entry in enumerate(gens):
        gid = f"gen-{i + 1}"
        existing = await db.get(Generation, gid)

        if isinstance(entry, dict) and "url" in entry:
            detail = await fetch_json(entry["url"])
        else:
            detail = FALLBACK_GENERATIONS[i] if i < len(FALLBACK_GENERATIONS) else entry
        if not detail:
            continue

        name = detail.get("name", f"gen-{i + 1}").replace("-", " ").title()
        region = detail.get("main_region", {}).get("name", "unknown")
        groups = detail.get("version_groups", [])
        games = ", ".join(g["name"].replace("-", " ").title() for g in groups) if groups else "Various"
        species = [s["name"] for s in (detail.get("pokemon_species") or [])]
        dex_count = len(species)

        vals = {
            "name": name,
            "gen_number": i + 1,
            "date_utc": datetime(1996 + i * 3, 2, 27, 0, 0, 0, tzinfo=timezone.utc),
            "complete": True,
            "details": f"Region: {region.title()}. Games: {games}. Pokémon discovered: {dex_count}.",
            "region_name": region.title(),
            "games": games,
            "total_species": dex_count,
            "pokemon_species": species,
            "cached_at": datetime.now(timezone.utc),
        }
        if existing:
            await db.execute(update(Generation).where(Generation.id == gid).values(**vals))
        else:
            db.add(Generation(id=gid, **vals))
        count += 1

    await db.commit()
    print(f"Synced {count} generations")
    return count
