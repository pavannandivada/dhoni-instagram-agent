# Incremental implementation plan

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| 0 | repository, Docker PostgreSQL + pgvector, migrations, config, quality tooling | reproducible local database and passing checks |
| 1 | Google Sheets/Drive ingestion | normalized, hash-deduplicated source documents |
| 2 | embeddings and vector storage | dimension choice measured and stored with metadata |
| 3 | hybrid retrieval | precision and metadata-filter evaluation dataset |
| 4 | planner and specialized agents | strict tool calls and structured proposals |
| 5 | fact/quote validation and critic | unsupported and duplicate content rejected |
| 6 | Google Sheets HITL | risk-driven approval states and audit entries |
| 7 | Meta publishing | container workflow, idempotency, and audit trail |
| 8 | analytics and learning | minimum-sample reporting without automatic prompt drift |
| 9 | evaluation framework | regression suite for retrieval, grounding, safety, and tools |
| 10 | observability and portfolio hardening | operational dashboard, screenshots, and complete runbook |

Each phase is implemented, tested, documented, reviewed, and committed separately. Production integrations remain disabled until their phase-specific evaluations pass.
