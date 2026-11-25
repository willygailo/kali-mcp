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

## Scope & Host Guards
- NOT installed: `haiti`, `jwt_tool`. Use `hashid`, `john` (`john_crack`), `hashcat`, `/usr/share/wordlists/rockyou.txt`, Python 3 stdlib.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.
- Never send captured hashes or JWTs to external online services.

## Tactical Decision Tree
- **Unknown hash** -> `hashid -m -j '<hash>'` to get Hashcat `-m` and John `--format`:
  - `$krb5tgs$23$`=`-m 13100`/`krb5tgs`; `$krb5asrep$23$`=`-m 18200`/`krb5asrep`
  - `$2a$/$2y$`=`-m 3200`/`bcrypt`; NTLM 32hex=`-m 1000`/`NT`; NetNTLMv2=`-m 5600`/`netntlmv2`
- **Offline crack** -> save to `/tmp/hashes.txt` (`chmod 600`):
  - `john_crack` tool or `timeout 90s john --format=<fmt> --wordlist=/usr/share/wordlists/rockyou.txt /tmp/hashes.txt`
  - Check hits: `john --show /tmp/hashes.txt`
- **Rule pass** -> `timeout 120s hashcat -m <mode> /tmp/hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule --force`
- **SSH key / ZIP / PDF** -> `bash -c "ssh2john <key> > /tmp/k.hash"` (or `zip2john`/`pdf2john`) -> `john`
- **JWT (`eyJ...`)** -> decode: `python3 -c "import sys,json,base64; p=sys.argv[1].split('.'); d=lambda s: json.loads(base64.urlsafe_b64decode(s+'==='[:(4-len(s)%4)%4])); print(json.dumps({'header':d(p[0]),'payload':d(p[1])},indent=2))" "<JWT>"`
  - If `HS256` -> `timeout 60s john --format=HMAC-SHA256 --wordlist=/usr/share/wordlists/rockyou.txt /tmp/jwt.txt`
- **Plaintext creds found** -> pivot to `ad-kerberos-enum`, `infra-db-services-enum`, or `web-api-vhost-recon`.

## Timeout & False-Positive Guards
- Cap all `john`/`hashcat` at `60s-120s`; avoid huge rulesets on slow hashes (`bcrypt`, `scrypt`).
- 32-hex could be MD5, NTLM, or UUID—confirm from context before cracking.
- Run `john --show` first to avoid re-cracking stale potfile hits.

## Severity & Evidence Criteria
- **Critical**: Cracked privileged cred, weak JWT HMAC secret, `alg: none` accepted, unencrypted private key.
- **High**: Cracked user/AD hash, JWT missing `exp` or leaking PII, `RS256->HS256` key-confusion signal.
- **Medium**: Legacy weak hash (`MD5`/`SHA1`/`NTLM`) in storage, excessive token TTL.
- **Info**: Hash format only, non-sensitive JWT claims (`iss`, `iat`).
- **Redaction**: Mask cracked secrets, raw hashes, private keys, JWTs to `<prefix>...<last4>`.
