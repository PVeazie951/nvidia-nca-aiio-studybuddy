"""FastAPI entry point for the NVIDIA study buddy."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .config import settings
from .db import SessionLocal, engine, init_db
from .migrations import apply_migrations
from .models import LlmProfile, Topic
from .routes import router
from .syllabus import SEED_TOPICS


async def seed() -> None:
    async with SessionLocal() as session:
        existing = (await session.execute(select(Topic.slug))).scalars().all()
        have = set(existing)
        for order, item in enumerate(SEED_TOPICS):
            if item["slug"] not in have:
                session.add(Topic(sort_order=order, **item))
        profile = (await session.execute(select(LlmProfile).limit(1))).scalars().first()
        if not profile:
            from .llm import DEFAULT_PROMPTS

            session.add(LlmProfile(prompts=dict(DEFAULT_PROMPTS)))
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    await init_db()
    # create_all() never adds columns to an existing table.
    await apply_migrations(engine)
    await seed()
    yield


app = FastAPI(title="NVIDIA NCA-AIIO Study Buddy", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "nvidia-studybuddy"}
