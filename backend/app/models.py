"""SQLAlchemy models for study material, notes, and LLM settings."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Asset(Base):
    """A dropped/pasted screenshot or file, plus its extracted text."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(255), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(32), default="file")  # image | file | text
    stored_path: Mapped[str] = mapped_column(String(1024))
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    extraction_error: Mapped[str] = mapped_column(Text, default="")
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic: Mapped["Topic | None"] = relationship(back_populates="assets")


class Topic(Base):
    """A study topic from the NCA-AIIO syllabus."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    weight: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[int] = mapped_column(Integer, default=0)  # 0-5 self rating
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assets: Mapped[list[Asset]] = relationship(back_populates="topic")
    notes: Mapped[list["Note"]] = relationship(back_populates="topic")


class Note(Base):
    """A note the user writes, optionally generated with the LLM."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="user")  # user | llm
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic: Mapped["Topic | None"] = relationship(back_populates="notes")


class LlmProfile(Base):
    """An OpenAI-compatible endpoint plus per-feature prompt templates."""

    __tablename__ = "llm_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), default="default")
    base_url: Mapped[str] = mapped_column(String(512), default="http://127.0.0.1:11434/v1")
    model: Mapped[str] = mapped_column(String(255), default="")
    api_key: Mapped[str] = mapped_column(String(512), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    temperature: Mapped[float] = mapped_column(default=0.3)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1500)
    prompts: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
