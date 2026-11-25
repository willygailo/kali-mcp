---
name: web-api-vhost-recon
description: Fingerprint web stacks, discover virtual hosts, crawl SPAs/APIs, and run read-only parameter and vulnerability checks. Use when HTTP/HTTPS ports (80, 443, 3000, 5000, 8000, 8080, 8443, 9000) or web/API/VHost/WordPress targets appear.
category: web
triggers:
  ports: [80, 443, 3000, 5000, 8000, 8080, 8443, 9000]
  services: [http, https, http-proxy, http-alt]
  keywords: [web, api, vhost, subdomain, graphql, swagger, openapi, wordpress, sqli]
recommended_tools: [origin_dns_tls, tech_waf_fingerprint, subdomain_enum, vhost_fuzz, endpoint_crawl, param_discover, gobuster_scan, nikto_scan, wpscan_analyze, sqlmap_scan]
allowed_mode: read_only
---

# Web, API & Virtual Host Recon

## Scope & Host Guards
- **ALWAYS `httpx-toolkit`** (`/usr/bin/httpx-toolkit`) — NEVER bare `/usr/bin/httpx` (Python CLI).
- `subfinder`/`katana` may require `~/.pdtm`; prefer `origin_dns_tls`, `tech_waf_fingerprint`, `endpoint_crawl`, `gospider`, `hakrawler`, `gau`, `gobuster`.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`. Read-only only.

## Tactical Decision Tree
- **HTTP/HTTPS open** -> `origin_dns_tls` + `tech_waf_fingerprint` (or `timeout 20s httpx-toolkit -u <url> -sc -title -tech-detect -location`); add `.htb`/`.local` TLS SANs to `/etc/hosts`.
- **VHost/subdomain enum** -> `subdomain_enum` + `vhost_fuzz` (or `timeout 60s ffuf -u http://<host> -H "Host: FUZZ.<dom>" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -ac`).
- **SPA/API unknown**:
  - `endpoint_crawl` + `timeout 45s gospider -s <url> -d 2 -c 5 --js`
  - Probe `/openapi.json`, `/swagger.json`, `/graphql`, `/actuator`, `/v3/api-docs`
  - `timeout 60s ffuf -u <url>/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common-api-endpoints-mazen160.txt -ac`
- **WordPress** -> `wpscan_analyze` (passive/mixed, no brute force).
- **Params/forms found**:
  - `param_discover` or `timeout 45s arjun -u <url> -m GET,POST`
  - `sqlmap_scan` (`--batch --level=1 --risk=1 --banner --current-db`)
  - `timeout 30s dalfox url "<url>?p=test" --only-discovery --silence`
- **`.js`/`.js.map`/`.env`/`.git`** -> `secrets-vcs-config-audit`; JWTs/hashes -> `crypto-hash-jwt-triage`.

## Timeout & False-Positive Guards
- **Mandatory `-ac`** on every `ffuf` to auto-filter wildcard/soft-404s; start with `5000`-entry wordlists.
- Enforce `--batch` (`sqlmap`), `--silence --only-discovery` (`dalfox`), `--max-time 10` (`curl`), `timeout 20s-90s`.
- Compare response size/words/title against a nonexistent path before reporting hits.

## Severity & Evidence Criteria
- **Critical**: Verified SQLi (`--current-db`), unauthenticated admin/RCE, exposed `/actuator/heapdump`.
- **High**: Reflected XSS on sensitive route, unauthenticated GraphQL/OpenAPI data leak, vulnerable WP plugin.
- **Medium**: Auth-gated VHost/admin, verbose stack traces, missing API security headers.
- **Info**: Stack fingerprint, public TLS SANs, benign `robots.txt`/`health`.
- **Redact**: Mask cookies, `Authorization`, API keys, JWTs to `<prefix>...<last4>`.
