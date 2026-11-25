---
name: crypto-hash-jwt-triage
description: Identify unknown hashes, run authorized offline wordlist cracking, and decode or audit JWT headers and claims locally. Use when hashes, NTLM, Kerberos tickets, bcrypt, Base64 blobs, or JWT tokens (eyJ...) are encountered.
category: crypto
triggers:
  ports: []
  services: []
  keywords: [hash, md5, sha1, sha256, ntlm, bcrypt, jwt, eyj, krb5tgs, krb5asrep, token, base64]
recommended_tools: [john_crack, execute_command]
allowed_mode: read_only
---

# Crypto, Hash & JWT Triage

## Environment Notes
- `haiti` and `jwt_tool` are **NOT installed** on this host.
- Use `hashid`, `john`, `hashcat`, `/usr/share/wordlists/rockyou.txt`, and Python 3 stdlib for Base64URL JWT decoding.
- Perform all cracking and decoding locally/offline on authorized lab artifacts; redact cracked secrets in reports.

## Step 1: Hash Identification
- Classify unknown hash formats before selecting a cracker mode:
  - `hashid -m -j '<hash>'` (shows both Hashcat `-m` mode and John `--format`).
- Common lab/HTB prefixes & modes:
  - `$krb5tgs$23$` -> Hashcat `-m 13100` / John `krb5tgs`
  - `$krb5asrep$23$` -> Hashcat `-m 18200` / John `krb5asrep`
  - `$2a$` / `$2b$` / `$2y$` (bcrypt) -> Hashcat `-m 3200` / John `bcrypt`
  - NTLM (32 hex) -> Hashcat `-m 1000` / John `NT`
  - NetNTLMv2 (`user::DOMAIN:...`) -> Hashcat `-m 5600` / John `netntlmv2`

## Step 2: Authorized Offline Cracking
- Save hashes to a dedicated lab temp file (`/tmp/hashes.txt`, chmod `600`).
- **John the Ripper** (`john_crack` tool or CLI):
  - `john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/hashes.txt`
  - `john --format=<fmt> --wordlist=/usr/share/wordlists/rockyou.txt /tmp/hashes.txt`
  - `john --show /tmp/hashes.txt`
- **Hashcat** (fast GPU/CPU rules when needed):
  - `hashcat -m <mode> /tmp/hashes.txt /usr/share/wordlists/rockyou.txt --force`
  - Add `-r /usr/share/hashcat/rules/best64.rule` for quick rule-based coverage.
- For SSH private keys (`BEGIN OPENSSH PRIVATE KEY`) or ZIP/PDF archives: use `ssh2john`, `zip2john`, or `pdf2john` before `john`.

## Step 3: Local JWT & Base64URL Inspection (Python Stdlib)
- Decode header & payload offline without network transmission:
  - `python3 -c "import sys,json,base64; p=sys.argv[1].split('.'); d=lambda s: json.loads(base64.urlsafe_b64decode(s+'==='[:(4-len(s)%4)%4])); print(json.dumps({'header':d(p[0]),'payload':d(p[1])},indent=2))" "<JWT>"`
- Check JWT security indicators:
  - Header: `alg` (`none`, `HS256` vs `RS256` key-confusion candidate), `kid` (path/SQLi pattern), `jku`/`x5u`/`jwk` URLs.
  - Payload: `exp`/`nbf`/`iat` validity, `iss`/`aud`, role/admin/tenant claims, leaked internal IDs or emails.
- If a weak HMAC secret is suspected on an authorized lab JWT, test offline with `hashcat -m 16500` or `john --format=HMAC-SHA256` against `rockyou.txt`.
