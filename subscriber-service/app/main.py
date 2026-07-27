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

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

EVENT_TEMPLATES = {
    "generation": "New generation discovered: {name} on {date}",
    "rare": "Rare Pokémon spotted: {name}",
    "region": "New region announced: {name}",
}


async def check_new_events():
    async with async_session() as db:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT id, name, date_utc, complete FROM generations WHERE complete = true ORDER BY date_utc DESC LIMIT 5")
        )
        generations = result.fetchall()

        result2 = await db.execute(
            select(Subscriber)
        )
        subscribers = result2.scalars().all()

        for gen in generations:
            for sub in subscribers:
                if "generation" in (sub.event_types or []):
                    date_str = gen.date_utc.strftime("%Y-%m-%d %H:%M UTC") if gen.date_utc else "TBD"
                    message = f"New generation discovered: {gen.name} on {date_str}"
                    existing = await db.execute(
                        select(Alert).where(
                            Alert.subscriber_id == sub.id,
                            Alert.event_type == "generation",
                            Alert.message == message,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(Alert(
                            subscriber_id=sub.id,
                            event_type="generation",
                            message=message,
                            link=f"/generations/{gen.id}",
                        ))
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
    allow_origins=CORS_ORIGINS.split(",") if CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
