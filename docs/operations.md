# Operations runbook

## Local database lifecycle

```bash
cp .env.example .env
docker compose --env-file .env -f docker/docker-compose.yml up -d
.venv/bin/python scripts/migrate.py
.venv/bin/python scripts/healthcheck.py
```

Use `docker compose --env-file .env -f docker/docker-compose.yml logs -f postgres` to inspect the database. Stop the stack with `down`; add `-v` only when intentionally deleting all local database data.

## Migration policy

- Migrations are append-only once shared.
- Assign a unique four-digit prefix.
- Test a migration on a fresh database and a database with all prior migrations applied.
- Do not rewrite a migration that may already have run elsewhere.

## Reliability baseline

Subsequent integration phases must add timeouts, bounded exponential backoff with jitter, rate limits, typed errors, and idempotency keys. Do not retry validation or authentication failures. Publishing must verify container readiness and store the resulting Instagram media ID before it can be retried.
