# Security model

## Secrets

- Store real secrets only in local environment variables, an untracked `.env`, or a production secret manager.
- Commit placeholders only in `.env.example`.
- Never put credentials in Git history, README examples, n8n exports, prompts, screenshots, test fixtures, logs, or issue comments.
- Rotate a secret if it is ever committed or exposed.

## Least authority

- Use separate service credentials for Google, Gemini, Meta, n8n, and PostgreSQL.
- Restrict the Meta token to the intended business account and publishing capability.
- Run PostgreSQL as a non-superuser application role after bootstrap.

## Content safety controls

The system must fail closed for unverified quotes, unsupported claims, fact conflicts, unknown rights, and duplicate publication attempts. LLM output is untrusted input until deterministic checks pass.

Before production, run n8n's security audit and record remediations in the operations log. External binary storage is not part of this project baseline.
