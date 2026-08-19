#!/usr/bin/env python3
"""Apply the ordered SQL migrations to the configured local database."""

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.migrations import migrate


def main() -> None:
    applied = migrate(Settings())
    message = ", ".join(applied) if applied else "none"
    print(f"Applied migrations: {message}")


if __name__ == "__main__":
    main()
