# Contributing

## Branching

- `main` is the protected, releasable branch.
- `develop` is the integration branch once concurrent feature work begins.
- Use `feature/<scope>` for a meaningful, independently reviewable change; for example, `feature/rag-ingestion`.

## Before opening a pull request

Run the documented lint, formatting, type, and test checks. Keep migrations append-only and document changes that affect prompt versions, retrieval behavior, risk rules, rights controls, or external integrations.

Do not commit `.env`, credentials, downloaded source assets, or n8n workflow exports containing credentials.
