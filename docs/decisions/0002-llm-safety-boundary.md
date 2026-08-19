# ADR 0002: LLMs propose; deterministic systems authorize

- **Status:** Accepted
- **Decision:** Use models for planning, synthesis, classification, and caption drafting only. Validation, asset-rights checks, approval decisions, duplicate prevention, and publishing idempotency are deterministic controls.

## Consequences

Agent proposals must use strict schemas and cite internal evidence identifiers. A proposal cannot directly invoke publication or mark an asset as rights-cleared. Unknown or conflicting evidence produces a typed failure and a human-review path.
