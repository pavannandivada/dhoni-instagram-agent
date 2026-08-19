from pathlib import Path

from dhoni_instagram_agent.migrations import discover_migrations


def test_discover_migrations_orders_by_version(tmp_path: Path) -> None:
    (tmp_path / "0002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "0001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "ignored.sql").write_text("SELECT 0;", encoding="utf-8")

    migrations = discover_migrations(tmp_path)

    assert [migration.version for migration in migrations] == ["0001", "0002"]
