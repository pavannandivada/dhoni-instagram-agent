"""CLI entry point for the database health check."""

from __future__ import annotations

import sys

import psycopg

from dhoni_instagram_agent.config import Settings


def main() -> None:
    try:
        with psycopg.connect(Settings().database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.execute(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                    ")"
                )
                extension_row = cursor.fetchone()
    except psycopg.Error as error:
        print(
            f"Database health check failed: {error.__class__.__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    vector_enabled = extension_row is not None and bool(extension_row[0])

    if not vector_enabled:
        print(
            "Database health check failed: vector extension is unavailable",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print("Database health check passed: PostgreSQL and pgvector are ready.")


if __name__ == "__main__":
    main()
