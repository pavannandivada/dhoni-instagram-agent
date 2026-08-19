"""Small, explicit SQL migration runner for the local platform database."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import psycopg

from dhoni_instagram_agent.config import Settings

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MIGRATIONS_DIR = REPOSITORY_ROOT / "db" / "migrations"


@dataclass(frozen=True)
class Migration:
    """An ordered SQL migration discovered from the repository."""

    version: str
    path: Path


def discover_migrations(directory: Path = DEFAULT_MIGRATIONS_DIR) -> list[Migration]:
    """Return numerically ordered migration files and reject duplicate versions."""

    migrations = [
        Migration(version=path.name.split("_", maxsplit=1)[0], path=path)
        for path in directory.glob("[0-9][0-9][0-9][0-9]_*.sql")
    ]
    migrations.sort(key=lambda migration: migration.version)
    versions = [migration.version for migration in migrations]
    if len(versions) != len(set(versions)):
        raise ValueError(f"Duplicate migration version in {directory}")
    return migrations


def apply_migrations(
    connection: psycopg.Connection[tuple[object, ...]],
    migrations: Iterable[Migration],
) -> list[str]:
    """Apply each unseen migration exactly once and return applied versions."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute("SELECT version FROM schema_migrations")
        applied_versions = {row[0] for row in cursor.fetchall()}

        newly_applied: list[str] = []
        for migration in migrations:
            if migration.version in applied_versions:
                continue
            cursor.execute(migration.path.read_text(encoding="utf-8"))
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (migration.version,),
            )
            newly_applied.append(migration.version)
    connection.commit()
    return newly_applied


def migrate(settings: Settings, directory: Path = DEFAULT_MIGRATIONS_DIR) -> list[str]:
    """Open the configured database and apply repository migrations."""

    with psycopg.connect(settings.database_url) as connection:
        return apply_migrations(connection, discover_migrations(directory))
