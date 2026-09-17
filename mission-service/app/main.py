import os
import asyncio
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from app.database import init_db, close_db, async_session
from app.models import Generation
from app.routes import router
from app.poke_client import sync_generations, sync_pokemon

DEFAULT_CORS_ORIGINS = "http://localhost:3000"


def _parse_cors_origins() -> list:
    raw = os.getenv("CORS_ORIGINS") or os.getenv("FRONTEND_URL") or DEFAULT_CORS_ORIGINS
    raw = raw.strip()
    if raw == "*" or not raw:
        return [DEFAULT_CORS_ORIGINS]
    origins = [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]
    return origins or [DEFAULT_CORS_ORIGINS]


CORS_ORIGINS = _parse_cors_origins()
SYNC_INTERVAL_S = int(os.getenv("SYNC_INTERVAL_S", "3600"))
SYNC_ADVISORY_LOCK_KEY = int(os.getenv("SYNC_LOCK_KEY", "420001"))


async def _needs_seed(db) -> bool:
    return (await db.scalar(select(func.count()).select_from(Generation))) == 0


async def _try_sync_once() -> bool:
    """Returns True if this replica won the advisory lock and synced."""
    async with async_session() as db:
        try:
            got = (await db.execute(
                select(func.pg_try_advisory_xact_lock(SYNC_ADVISORY_LOCK_KEY))
            )).scalar()
        except Exception:
            got = True  # Non-Postgres (tests): proceed without lock.
        if not got:
            print("Sync skipped: another replica holds the lock")
            return False
        await sync_generations(db)
        await sync_pokemon(db)
        return True


async def background_sync():
    await asyncio.sleep(random.uniform(0, 30))  # jitter: avoid herd on deploy
    while True:
        try:
            await _try_sync_once()
        except Exception as e:
            print(f"Sync error: {e}")
        await asyncio.sleep(SYNC_INTERVAL_S + random.uniform(0, 60))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Seed-once only; never delete. Upserts in poke_client.py handle updates.
    async with async_session() as db:
        if await _needs_seed(db):
            try:
                await _try_sync_once()
            except Exception as e:
                print(f"Initial sync failed (will retry in background): {e}")
        else:
            print("DB already seeded, skipping initial sync")
    task = asyncio.create_task(background_sync())
    yield
    task.cancel()
    await close_db()


app = FastAPI(title="PokéMission Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials="*" not in CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router)
