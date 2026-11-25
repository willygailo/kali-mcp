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

## Environment Notes
- `ssh-audit` and `mongosh` are **NOT installed** on this host — use `nmap --script ssh2-enum-algos` / `ssh -G` / banner grab for SSH, and `nmap --script mongodb-info` or Python/TCP banner check for MongoDB.
- Keep all checks strictly read-only: no writes, `FLUSHALL`, `SET`, `CONFIG SET`, file uploads, or credential brute-forcing.

## Step 1: Service Fingerprinting & Version Correlation
- Run targeted `nmap_scan` (`-sCV -sV -p <ports>`) to obtain exact software + version banners.
- Correlate every exact product/version immediately:
  - `searchsploit --json "<software> <version>"` (or `searchsploit` MCP tool)
  - `cve_lookup` MCP tool (`cve-mcp`) for authoritative CVE/CVSS/CPE context.

## Step 2: Core Network & File Services (Read-Only)
- **FTP (21)**: Check anonymous login (`curl -sS ftp://anonymous:anonymous@<IP>/` or `nmap --script ftp-anon,ftp-syst -p 21 <IP>`).
- **SSH (22)**: Grab banner & hostkey/kex algorithms (`ssh-keyscan <IP>`, `nmap -p 22 --script ssh2-enum-algos,ssh-hostkey <IP>`).
- **DNS (53)**: Test zone transfer (`dig @<IP> <domain> AXFR`) and version (`dig @<IP> version.bind TXT CHAOS`).
- **RPC / NFS (111 / 2049)**: List exports (`showmount -e <IP>`, `rpcinfo -p <IP>`). Do not mount without scope need; mount `-o ro,nolock` if reading authorized lab shares.
- **SNMP (161/udp)**: Sweep community strings (`onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt <IP>`) then walk (`snmpwalk -v2c -c public <IP> NET-SNMP-EXTEND-MIB::nsExtendOutputFull` or `1.3.6.1.2.1.1`).

## Step 3: Databases, Caches & Docker API (Read-Only)
- **Redis (6379)**: `redis-cli -h <IP> INFO server` and `KEYS *` / `CLIENT LIST` (read-only; never `CONFIG SET` or `SLAVEOF`).
- **PostgreSQL (5432)**: `psql -h <IP> -U postgres -c "SELECT version();" -c "\l"` (when default/discovered creds exist).
- **MySQL/MariaDB (3306)**: `mysql -h <IP> -u root -e "SELECT version(); SHOW DATABASES;"` (or `nmap --script mysql-info,mysql-empty-password -p 3306 <IP>`).
- **Elasticsearch (9200)**: `curl -sS http://<IP>:9200/_cat/indices?v` and `http://<IP>:9200/` (no index writes).
- **Memcached (11211)**: `printf "stats\r\nversion\r\nquit\r\n" | nc -nv -w 3 <IP> 11211`.
- **MongoDB (27017)**: `nmap -p 27017 --script mongodb-info,mongodb-databases <IP>`.
- **Docker API (2375/2376)**: `curl -sS http://<IP>:2375/version` and `http://<IP>:2375/containers/json` (read-only inspect; never spawn containers).
