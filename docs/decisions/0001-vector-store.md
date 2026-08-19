# ADR 0001: Start locally with PostgreSQL + pgvector

- **Status:** Accepted for Phase 0, subject to benchmark review in Phase 2
- **Decision:** Use self-hosted PostgreSQL with pgvector as the initial knowledge and retrieval store.

## Context

The platform needs relational approval/audit data, metadata filters, vector similarity, low operational complexity, and a credible local portfolio setup. The proposed default is PostgreSQL + pgvector, but this choice should be evidence-led rather than assumed permanent.

## Rationale

It keeps transactional content state and embeddings in one backup, permissions, migration, and Docker surface. It avoids a paid SaaS dependency while leaving an explicit retrieval boundary for later replacement.

## Alternatives considered

- Managed vector services (for example, cloud-native vector search): potentially stronger scale and operations, but add cloud cost, credentials, and deployment complexity.
- Dedicated vector databases: potentially useful for very large or specialized retrieval workloads, but add another durable service without a demonstrated Phase 0 need.

## Consequences and review gate

Phase 2 will benchmark pgvector against the most relevant alternative using the evaluation dataset, representative metadata filters, target latency, ingestion volume, retrieval precision, operating cost, and backup/recovery complexity. A migration is justified only if it materially improves agreed metrics.
