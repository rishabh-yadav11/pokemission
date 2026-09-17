import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import init_db, close_db, async_session
from app.routes import router
from app.models import Subscriber, Alert

DEFAULT_CORS_ORIGINS = "http://localhost:3000"


def _parse_cors_origins() -> list:
    raw = os.getenv("CORS_ORIGINS") or os.getenv("FRONTEND_URL") or DEFAULT_CORS_ORIGINS
    raw = raw.strip()
    if raw == "*" or not raw:
        return [DEFAULT_CORS_ORIGINS]
    origins = [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]
    return origins or [DEFAULT_CORS_ORIGINS]


CORS_ORIGINS = _parse_cors_origins()

EVENT_TEMPLATES = {
    "generation": "New generation discovered: {name} on {date}",
    "rare": "Rare Pokémon spotted: {name}",
    "region": "New region announced: {name}",
}


async def check_new_events():
    async with async_session() as db:
        from sqlalchemy import text
        # Advisory lock: safe during rolling-update / multi-replica overlap.
        try:
            await db.execute(text("SELECT pg_advisory_xact_lock(hashtext('subscriber-check'))"))
        except Exception:
            pass
        result = await db.execute(
            text("SELECT id, name, date_utc FROM generations WHERE complete = true ORDER BY date_utc DESC LIMIT 5")
        )
        generations = result.fetchall()
        if not generations:
            return

        # Only subscribers interested in generation events (DB-side filter).
        try:
            result2 = await db.execute(
                select(Subscriber).where(Subscriber.event_types.contains(["generation"]))
            )
        except Exception:
            # Fallback for DBs without JSONB contains (e.g. SQLite tests).
            result2 = await db.execute(select(Subscriber))
        subscribers = [s for s in result2.scalars().all() if "generation" in (s.event_types or [])]
        if not subscribers:
            return

        links = [f"/generations/{g.id}" for g in generations]
        sub_ids = [s.id for s in subscribers]
        # Single batched existence check replaces 5*N per-cell selects.
        existing_rows = await db.execute(
            select(Alert.subscriber_id, Alert.link).where(
                Alert.event_type == "generation",
                Alert.link.in_(links),
                Alert.subscriber_id.in_(sub_ids),
            )
        )
        existing = set(existing_rows.all())
        rows = []
        for gen in generations:
            link = f"/generations/{g.id}"
            date_str = gen.date_utc.strftime("%Y-%m-%d %H:%M UTC") if gen.date_utc else "TBD"
            for sub in subscribers:
                if (sub.id, link) not in existing:
                    rows.append({
                        "subscriber_id": sub.id,
                        "event_type": "generation",
                        "message": f"New generation discovered: {gen.name} on {date_str}",
                        "link": link,
                    })
        if not rows:
            return
        # Idempotent insert: concurrent workers cannot duplicate (UNIQUE + DO NOTHING).
        try:
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            await db.execute(
                pg_insert(Alert).values(rows).on_conflict_do_nothing(
                    index_elements=["subscriber_id", "event_type", "link"]
                )
            )
            await db.commit()
        except Exception:
            # Fallback for non-Postgres (tests): best-effort plain insert.
            await db.rollback()
            for row in rows:
                db.add(Alert(**row))
            await db.commit()


async def background_check():
    while True:
        try:
            await check_new_events()
        except Exception as e:
            print(f"Event check error: {e}")
        await asyncio.sleep(120)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(background_check())
    yield
    task.cancel()
    await close_db()


app = FastAPI(title="PokéMission Subscriber Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials="*" not in CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router)