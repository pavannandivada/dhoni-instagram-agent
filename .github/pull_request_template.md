## Summary

<!-- What changed and why? -->

## Validation

- [ ] Ruff check passes
- [ ] Ruff format check passes
- [ ] Mypy passes
- [ ] Tests pass
- [ ] No real secrets or credentials are included
- [ ] No production database, Cloud Run, GCS, Meta, or scheduler changes are required unless explicitly called out

## Security / production impact

- [ ] No authentication, authorization, publishing, licensing, or secret-handling behavior changed
- [ ] If security-sensitive behavior changed, `SECURITY.md` and the relevant tests/documentation were reviewed
- [ ] If a migration is included, it is append-only and backward-compatible where required

## Reviewer notes

<!-- Mention risks, rollout/rollback notes, or anything that needs special review. -->
