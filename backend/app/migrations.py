"""Additive schema migrations.

SQLAlchemy's create_all() only creates missing tables -- it never adds columns
to an existing one. This module applies the handful of additive column changes
this app has made, so an existing database keeps working without a manual
migration or a drop/recreate.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

log = logging.getLogger("studybuddy.migrations")

# (table, column, DDL type, default clause)
ADDITIVE_COLUMNS: list[tuple[str, str, str, str]] = [
    ("llm_profiles", "supports_vision", "BOOLEAN", "FALSE"),
    ("llm_profiles", "last_probe", "JSONB", "'{}'::jsonb"),
]


async def apply_migrations(engine: AsyncEngine) -> list[str]:
    """Add any missing columns. Returns the list of columns actually added."""
    applied: list[str] = []
    async with engine.begin() as conn:
        for table, column, coltype, default in ADDITIVE_COLUMNS:
            exists = await conn.scalar(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = :t AND column_name = :c"
                ),
                {"t": table, "c": column},
            )
            if exists:
                continue
            await conn.execute(
                text(
                    f'ALTER TABLE {table} ADD COLUMN {column} {coltype} '
                    f"NOT NULL DEFAULT {default}"
                )
            )
            applied.append(f"{table}.{column}")
            log.info("added column %s.%s", table, column)
    return applied
