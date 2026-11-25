---
name: infra-db-services-enum
description: Enumerate infrastructure, DNS, SNMP, NFS, Docker, and database services and correlate versions against Exploit-DB and CVE databases. Use when ports 21, 22, 53, 111, 161, 2049, 2375, 3306, 5432, 6379, 9200, 11211, or 27017 are open or CVEs/searchsploit are needed.
category: infrastructure
triggers:
  ports: [21, 22, 53, 111, 161, 2049, 2375, 3306, 5432, 6379, 9200, 11211, 27017]
  services: [ftp, ssh, domain, rpcbind, snmp, nfs, mysql, postgresql, redis, elasticsearch, mongodb]
  keywords: [ftp, ssh, snmp, nfs, redis, postgres, mysql, mongodb, elasticsearch, docker, cve, searchsploit]
recommended_tools: [nmap_scan, searchsploit, cve_lookup, execute_command]
allowed_mode: read_only
---

# Infrastructure, Databases & CVE Enumeration

## Scope & Host Guards
- NOT installed: `ssh-audit`, `mongosh`. Use `nmap --script ssh2-enum-algos`/`ssh-keyscan`, `nmap --script mongodb-info`.
- Read-only: no `FLUSHALL`, `SET`, `CONFIG SET`, container spawns, or brute-forcing.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.

## Tactical Decision Tree
- **Any service banner** -> `nmap_scan` (`-sCV -sV -Pn -p <ports>`) -> `searchsploit` + `cve_lookup` per version.
- **FTP (21)** -> `timeout 15s curl -sS --max-time 10 ftp://anonymous:anonymous@<IP>/` + `nmap -Pn -p 21 --script ftp-anon,ftp-syst <IP>`
- **SSH (22)** -> `timeout 15s ssh-keyscan -T 5 <IP>` + `nmap -Pn -p 22 --script ssh2-enum-algos,ssh-hostkey <IP>`
- **DNS (53)** -> `timeout 15s dig +time=5 +tries=1 @<IP> <dom> AXFR` + `dig +time=5 @<IP> version.bind TXT CHAOS`
- **RPC/NFS (111/2049)** -> `timeout 15s showmount -e <IP>`; `rpcinfo -p <IP>` (mount `-o ro,nolock` only if authorized)
- **SNMP (161/udp)** -> `timeout 30s onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt <IP>` -> `timeout 30s snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.1`
- **Redis/ES/Docker/Memcached** -> `timeout 10s redis-cli -h <IP> INFO server`; `curl -sS --max-time 10 http://<IP>:9200/_cat/indices?v`; `curl -sS --max-time 10 http://<IP>:2375/containers/json`; `bash -c "printf 'stats\r\nquit\r\n' | nc -w 3 <IP> 11211"`
- **MySQL/Postgres/Mongo** -> `nmap -Pn -p 3306 --script mysql-info,mysql-empty-password <IP>`; `timeout 15s psql -h <IP> -U postgres -c "SELECT version();"`; `nmap -Pn -p 27017 --script mongodb-info,mongodb-databases <IP>`
- **Creds/configs/hashes** -> pivot to `secrets-vcs-config-audit` or `crypto-hash-jwt-triage`.

## Timeout & False-Positive Guards
- Pass `-Pn`, `--max-time 10` (`curl`), `-w 3` (`nc`), `timeout 10s-30s`; keep SNMP to `common-snmp-community-strings.txt`; check OS backports before flagging CVEs.

## Severity & Evidence Criteria
- **Critical**: Unauth Docker API, open Redis/Mongo/ES with data, RCE CVE (`CVSS >= 9.0`), world-readable NFS keys.
- **High**: Anonymous FTP sensitive files, DNS AXFR dump, writable SNMP `private` community.
- **Medium**: Weak SSH kex/ciphers, SNMP `public` process leak, unauthenticated Memcached stats.
- **Info/Redact**: Patched banners, closed anon access. Mask passwords, SSH keys, URIs to `<prefix>...<last4>`.