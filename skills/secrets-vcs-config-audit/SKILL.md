---
name: secrets-vcs-config-audit
description: Audit exposed VCS metadata, dotfiles, JS bundles, and source maps for leaked credentials with entropy filtering and mandatory redaction. Use when .env, .git, .js.map, config files, API keys, or tokens are suspected or found.
category: secrets
triggers:
  ports: []
  services: [http, https]
  keywords: [secret, token, api key, .env, .git, .js.map, config, credential, trufflehog, gitleaks]
recommended_tools: [secret_exposure_scan, endpoint_crawl, execute_command]
allowed_mode: read_only
---

# Secrets, VCS & Config Audit (Read-Only)

## Trigger & Scope
- Activate when web crawling, directory fuzzing, or error traces expose `.git/`, `.env`, `.js.map`, backup configs (`.bak`, `.old`, `.swp`), or high-entropy strings in JS/JSON/YAML.
- Verified tools: `secret_exposure_scan`, `trufflehog`, `gitleaks`, `js-beautify`, `curl`, `python3`.

## Step 1: Automated Exposure & Local Artifact Scan
- Remote target probe: run `secret_exposure_scan` against each discovered base URL/VHost.
- Local downloaded bundles, `.git` mirrors, or repos:
  - `gitleaks detect --source <dir> --no-git --redact` (or omit `--no-git` on cloned/mirrored `.git` repos).
  - `trufflehog filesystem <dir> --only-verified` (or omit `--only-verified` in offline labs, then filter manually).
- Unminify dense JS bundles before regex/entropy inspection:
  - `js-beautify bundle.min.js -o bundle.pretty.js`

## Step 2: `.git` & `.js.map` Read-Only Inspection
- Verify `.git` exposure cleanly: `curl -sS <url>/.git/HEAD` (expect `ref: refs/heads/...`) and `<url>/.git/config`.
- Inspect local/mirrored `.git` objects & history without modifying refs:
  - `git -C <repo> log --oneline -n 30`
  - `git -C <repo> log -p -n 10 --all` (pipe to `grep -E` for keys/URIs/passwords).
- If `.js.map` is accessible, extract `sources` and `sourcesContent` with Python `json` module to inspect unminified source paths, internal URLs, and dev configs.

## Step 3: Entropy & False-Positive Filtering
- Check Shannon entropy (`> 4.5` bits/char for base64/hex tokens >= 20 chars) paired with nearby context (`secret`, `token`, `key`, `dsn`, `password`, `authorization`).
- **Drop false positives immediately**:
  - SRI hashes (`sha256-`, `sha384-`, `sha512-`), Webpack/Vite chunk hashes, UUIDv4 IDs.
  - Base64 fonts/SVGs/images (`data:image/...`), i18n keys, CSS hashes.
  - Public client IDs (`pk_test_`, `pk_live_`, reCAPTCHA site keys, public OAuth `client_id`, Sentry DSNs) and docs placeholders (`YOUR_API_KEY`, `AKIAIOSFODNN7EXAMPLE`).

## Step 4: Mandatory Redaction & Minimal Liveness Check
- **Mandatory Redaction**: Never print raw secrets in summaries or reports — mask to `<prefix>...<last4>` (or `****` for short strings).
- Confirm candidate secrets using only the smallest non-mutating read-only check:
  - Cloud/SaaS tokens: read-only identity/account call (`STS GetCallerIdentity`, `GET /user`, `auth.test`, `GET /v1/models`).
  - DB URIs: connect/version/ping handshake only (`SELECT version();` / `PING`) — no table dumps.
  - JWTs / PEM keys: local decode or fingerprint inspection (`crypto-hash-jwt-triage`).
