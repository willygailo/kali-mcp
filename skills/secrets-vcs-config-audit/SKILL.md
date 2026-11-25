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

## Scope & Host Guards
- Verified tools: `secret_exposure_scan`, `endpoint_crawl`, `trufflehog`, `gitleaks`, `js-beautify`, `curl`, `python3`, `git`.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.
- Strictly read-only: never alter git refs, push, or trigger write/billing API endpoints with found tokens.

## Tactical Decision Tree
- **If web/VHost URL found** -> `secret_exposure_scan` + `timeout 10s curl -sS --max-time 8 <url>/.git/HEAD`
- **If `.git/HEAD` returns `ref: refs/heads/`**:
  - Inspect read-only mirror: `timeout 60s gitleaks detect --source <dir> --redact`
  - History search: `bash -c "git -C <repo> log -p -n 10 --all | grep -iE 'key|secret|token|pass|dsn' | head -n 80"`
- **If local dir without `.git`**:
  - `timeout 60s gitleaks detect --source <dir> --no-git --redact`
  - `timeout 60s trufflehog filesystem <dir> --no-update`
- **If `.js` / `.js.map` exposed**:
  - `js-beautify bundle.min.js -o /tmp/bundle.pretty.js`
  - Extract `sources`/`sourcesContent` with `python3 -c` (`json`), then scan `/tmp/bundle.pretty.js`.
- **If token/DB URI/JWT found** -> smallest read-only check (`GET /user`, `STS GetCallerIdentity`, `SELECT version();`) or pivot to `crypto-hash-jwt-triage`.

## Timeout & False-Positive Guards
- Enforce `--max-time 8` (`curl`), `--redact` (`gitleaks`), `--no-update` (`trufflehog`), `timeout 60s`, and `git log -n 10`.
- Require Shannon entropy `> 4.5` (base64/hex `>= 20` chars) + nearby key/secret context.
- Drop FPs immediately: SRI hashes (`sha256-`/`sha384-`/`sha512-`), bundler chunk hashes, UUIDv4, `data:image/...`, public keys (`pk_test_`, `pk_live_`, reCAPTCHA, public `client_id`, Sentry DSNs), and doc samples (`AKIAIOSFODNN7EXAMPLE`, `YOUR_API_KEY`).

## Severity & Evidence Criteria
- **Critical**: Verified live admin/cloud/DB/signing credential (`.env` root DB URI, AWS `AKIA...` + secret, private PEM, active `ghp_`/`sk_live_`).
- **High**: Exposed `.git` history or `.js.map` leaking unverified private secrets or privileged internal endpoints.
- **Medium**: Exposed internal non-secret config (`.git/config` remotes, debug flags, internal paths).
- **Info**: Public client IDs, SRI hashes, clean negative scans.
- **Redaction**: NEVER print raw secrets—mask every credential/token/key to `<prefix>...<last4>` (or `****` if `< 8` chars).
