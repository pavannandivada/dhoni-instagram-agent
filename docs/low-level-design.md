# Low-level design

## Phase 0 interfaces

`Settings` reads runtime configuration from environment variables or an untracked `.env` file and exposes a percent-encoded PostgreSQL URL. It never writes secrets to disk.

`discover_migrations(directory) -> list[Migration]` accepts only `NNNN_name.sql` files, orders them by version, and rejects duplicate versions.

`apply_migrations(connection, migrations) -> list[str]` records each successful migration in `schema_migrations`, making reruns idempotent.

`scripts/healthcheck.py` validates reachability and checks that `pgvector` has been enabled by migration `0001_extensions.sql`.

## Planned contracts

Later phases will use strict structured outputs. Retrieval will follow this shape:

```json
{
  "results": [
    {
      "knowledge_id": "FACT-ODI-001",
      "content": "…",
      "score": 0.91,
      "source": "ICC",
      "source_url": "https://…",
      "metadata": {}
    }
  ]
}
```

No agent will receive an unbounded data dump. It will request an explicit tool, receive a small evidence set, and return a schema-validated proposal with its selected source and asset identifiers.
