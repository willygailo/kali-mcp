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

## Kali Environment Traps
- **ALWAYS use `httpx-toolkit`** (`/usr/bin/httpx-toolkit`) — NEVER bare `/usr/bin/httpx` (Python CLI).
- Use `vhost_fuzz` or `ffuf -ac` (auto-calibration) so wildcard/catch-all virtual hosts do not flood results.
- Note `subfinder`/`katana` may depend on `~/.pdtm`; use `gospider`, `hakrawler`, `gau`, and `gobuster` via `execute_command` if needed.

## Step 1: Origin, DNS, TLS & Stack Fingerprint
- Run `origin_dns_tls` to inspect `A`/`AAAA`/`CNAME`/`TXT`, WHOIS ASN, TLS CN/SANs, and HTTP `Location:` redirects.
- Run `tech_waf_fingerprint` (or `httpx-toolkit -u <url> -sc -title -tech-detect -location`, `whatweb <url>`, `wafw00f <url>`).
- Record any `.htb`/`.local`/internal domain revealed in TLS SANs or `Location:` headers for `/etc/hosts` before fuzzing.

## Step 2: Subdomain & Virtual Host Discovery
- Passive/active subdomain discovery: `subdomain_enum` or `gobuster dns -d <domain> -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt`.
- VHost fuzzing against direct IP or primary hostname:
  - `vhost_fuzz` or `ffuf -u http://<IP_or_host> -H "Host: FUZZ.<domain>" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -ac`
- Re-run stack fingerprinting on every newly discovered live VHost or non-standard web port (`3000`, `5000`, `8000`, `8080`, `8443`, `9000`).

## Step 3: Endpoint, SPA & API Surface Mapping
- Run `endpoint_crawl` or combine verified crawlers:
  - `gospider -s <url> -d 2 -c 5 --js`
  - `echo "<url>" | hakrawler -d 2 -subs`
  - `gau --subs <domain>` (public domain targets)
- Probe API schemas and debug routes (`/openapi.json`, `/swagger.json`, `/v3/api-docs`, `/graphql`, `/actuator`, `/health`).
- Directory & API fuzzing: `gobuster_scan` or `ffuf -u <url>/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common-api-endpoints-mazen160.txt -ac`.

## Step 4: Parameters & Read-Only Vulnerability Checks
- Discover hidden query/JSON parameters: `param_discover` or `arjun -u <url> -m GET,POST`.
- Web server misconfigs: `nikto_scan`.
- WordPress targets: `wpscan_analyze` (passive/mixed plugin & user enum, no password brute force).
- Read-only injection & XSS triage (never destructive):
  - `sqlmap_scan` with `--batch --level=1 --risk=1 --banner --current-db` (no `--os-shell` or writes).
  - `dalfox url "<url>?param=test" --only-discovery --silence` (reflection/XSS signal check only).

## Pivots
- If `.js`, `.js.map`, `.env`, or `.git` paths appear, trigger `secrets-vcs-config-audit`.
- If JWTs (`eyJ...`) or hashes appear in responses, trigger `crypto-hash-jwt-triage`.
