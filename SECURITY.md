# Security Policy

## Supported versions

Only the `main` branch is treated as the supported release line.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Use GitHub's private vulnerability reporting flow from the repository's **Security** tab when available. Include:

- a clear description of the issue;
- affected files or endpoints;
- reproduction steps or proof of concept;
- impact and likely attack path;
- any suggested mitigation.

Do not include credentials, access tokens, private URLs, or other secrets in a report.

## Public-repository rules

- Never commit real API keys, access tokens, passwords, service-account keys, database URLs, or `.env` files.
- Never add production credentials to tests, fixtures, screenshots, logs, issue comments, or workflow exports.
- Do not use GitHub Actions workflows that execute untrusted pull-request code with repository secrets.
- Changes to `main` must go through a pull request and required CI checks.
- External contributors should use forks and pull requests; they do not receive repository write access by default.

## Incident response

Any credential suspected of exposure must be revoked or rotated immediately, then removed from the repository and its history as appropriate.
