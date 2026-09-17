from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Generation, Pokemon

router = APIRouter(prefix="/api/mission", tags=["mission"])


@router.get("/health")
async def health():
    return {"status": "ok", "service": "mission-service"}


@router.get("/generations")
async def get_generations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Generation).order_by(desc(Generation.date_utc)).limit(50))
    gens = result.scalars().all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "gen_number": g.gen_number,
            "date_utc": g.date_utc.isoformat() if g.date_utc else None,
            "complete": g.complete,
            "details": g.details,
            "region_name": g.region_name,
            "games": g.games,
            "total_species": g.total_species,
            "pokemon_species": g.pokemon_species or [],
        }
        for g in gens
    ]


@router.get("/generations/{gen_id}/pokemon")
async def get_generation_pokemon(gen_id: str, db: AsyncSession = Depends(get_db)):
    g = await db.get(Generation, gen_id)
    if not g:
        raise HTTPException(status_code=404, detail="Generation not found")
    species_names = g.pokemon_species or []
    result = await db.execute(
        select(Pokemon).where(Pokemon.name.in_([s.title() for s in species_names]))
    )
    matches = result.scalars().all()
    name_map = {p.name.lower(): p for p in matches}
    ordered = []
    for s in species_names:
        p = name_map.get(s.lower())
        if p:
            ordered.append({
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "height_m": p.height_m,
                "mass_kg": p.mass_kg,
                "sprite_url": p.sprite_url,
                "base_experience": p.base_experience,
            })
    return ordered


@router.get("/generations/latest")
async def get_latest_generation(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Generation).order_by(desc(Generation.date_utc)).limit(1)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="No generations found")
    return {
        "id": g.id,
        "name": g.name,
        "gen_number": g.gen_number,
        "date_utc": g.date_utc.isoformat() if g.date_utc else None,
        "complete": g.complete,
        "details": g.details,
        "region_name": g.region_name,
        "games": g.games,
        "total_species": g.total_species,
    }


@router.get("/pokemon")
async def get_pokemon(
    response: Response,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # Set cache headers
    response.headers["Cache-Control"] = "public, max-age=60"
    response.headers["ETag"] = f'pokemon-{limit}-{offset}'

    result = await db.execute(select(Pokemon).limit(limit).offset(offset))
    all_pokemon = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "height_m": p.height_m,
            "mass_kg": p.mass_kg,
            "types_count": p.types_count,
            "abilities_count": p.abilities_count,
            "abilities": p.abilities,
            "base_experience": p.base_experience,
            "description": p.description,
            "sprite_url": p.sprite_url,
        }
        for p in all_pokemon
    ]


@router.get("/pokemon/{pokemon_id}")
async def get_one_pokemon(pokemon_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Pokemon, pokemon_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    return {
        "id": p.id,
        "name": p.name,
        "type": p.type,
        "height_m": p.height_m,
        "mass_kg": p.mass_kg,
        "types_count": p.types_count,
        "abilities_count": p.abilities_count,
        "abilities": p.abilities,
        "base_experience": p.base_experience,
        "description": p.description,
        "sprite_url": p.sprite_url,
    }


@router.get("/types")
async def get_types(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # DISTINCT query in SQL instead of loading full rows
    response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["ETag"] = "types-v1"

    result = await db.execute(
        select(func.distinct(Pokemon.type)).where(Pokemon.type.isnot(None))
    )
    types_raw = result.scalars().all()

    unique_types = set()
    for t in types_raw:
        for part in t.split("/"):
            part = part.strip()
            if part:
                unique_types.add(part)
    return [{"name": t} for t in sorted(unique_types)]