# High-level design

## Control plane versus knowledge layer

Google Sheets remains the human-friendly control plane for the content calendar, quotes, facts, assets, events, and approval state. PostgreSQL + pgvector will become the durable retrieval and audit layer. They are deliberately separate: a spreadsheet edit does not become trusted evidence until ingestion normalizes, hashes, validates, and indexes it.

## Responsibilities

| Component | Responsibility | Does not decide |
| --- | --- | --- |
| n8n | schedule, integrations, retries, routing, HITL notifications | factual truth or rights compliance |
| Ingestion | normalize source rows, hash content, conditionally embed | publish content |
| Retrieval | hybrid search, metadata filtering, reranking | invent evidence |
| Agents | choose tools and draft structured proposals | bypass safeguards |
| Validator/critic | source, conflict, duplication, schema, and policy checks | create missing source evidence |
| Publisher | media container lifecycle and idempotent publication | publish unapproved or high-risk content |

## Failure direction

Unknown source, unknown quote verification, uncertain asset rights, or evidence conflicts fail closed. A failure receives a typed reason and goes to an approval or failure queue rather than being retried as a creative-generation problem.
