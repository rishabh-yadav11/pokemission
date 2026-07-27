import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete

from app.database import init_db, close_db, async_session
from app.models import Generation, Pokemon
from app.routes import router
from app.poke_client import sync_generations, sync_pokemon

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


async def background_sync():
    while True:
        try:
            async with async_session() as db:
                gen_count = await sync_generations(db)
                poke_count = await sync_pokemon(db)
                print(f"Synced {gen_count} generations, {poke_count} Pokémon")
        except Exception as e:
            print(f"Sync error: {e}")
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as db:
        await db.execute(delete(Generation))
        await db.execute(delete(Pokemon))
        await db.commit()
        try:
            await sync_generations(db)
            await sync_pokemon(db)
        except Exception as e:
            print(f"Initial sync failed: {e}")
    task = asyncio.create_task(background_sync())
    yield
    task.cancel()
    await close_db()


app = FastAPI(title="PokéMission Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(",") if CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
