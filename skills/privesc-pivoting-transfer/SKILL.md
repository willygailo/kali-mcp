---
name: privesc-pivoting-transfer
description: Guide read-only post-foothold privilege escalation enumeration, exact PEASS/pspy binary paths, and authorized lab pivoting or file transfer setups. Use when privesc, sudo, SUID, capabilities, cron, linpeas, winpeas, pspy, ligolo, or chisel pivoting is needed.
category: privesc
triggers:
  ports: []
  services: [ssh, winrm]
  keywords: [privesc, privilege escalation, sudo, suid, capabilities, cron, pspy, linpeas, winpeas, pivot, tunnel, ligolo, chisel]
recommended_tools: [execute_command]
allowed_mode: read_only
---

# Post-Foothold PrivEsc Enum & Lab Pivoting

## Scope & Host Guards
- Local paths: LinPEAS (`/usr/share/peass/linpeas/linpeas.sh`), WinPEAS (`/usr/share/peass/winpeas/winPEASx64.exe`), pspy (`/usr/share/pspy/pspy64`), Chisel (`/usr/share/chisel-common-binaries/`), Ligolo (`ligolo-proxy`/`ligolo-agent`, NOT `ligolo-ng`), `socat`, `/usr/bin/pwncat` (`pwncat-cs` absent).
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.
- Ask before writing files to target disk or altering host state.

## Tactical Decision Tree
- **Linux foothold**:
  - `bash -c "id; uname -a; cat /etc/os-release; sudo -ln 2>/dev/null; ss -tulnp"`
  - `bash -c "find / -perm -4000 -type f 2>/dev/null; getcap -r / 2>/dev/null"`
- **Hidden cron/process** -> `timeout 45s /usr/share/pspy/pspy64 -pf -i 1000` or `/usr/share/peass/linpeas/linpeas.sh -q`
- **Windows foothold**: `whoami /all`; `cmdkey /list`; `reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated`; `/usr/share/peass/winpeas/winPEASx64.exe quiet servicesinfo userinfo`
- **Internal port/subnet**:
  - Ligolo: `ligolo-proxy -selfcert -laddr 0.0.0.0:11601` + `ligolo-agent -connect <KALI>:11601 -ignore-cert`
  - Chisel: `chisel server -p 8001 --reverse`; `socat TCP-LISTEN:8080,fork TCP:127.0.0.1:8080`
- **Internal DB/web/AD** -> pivot to `infra-db-services-enum`, `web-api-vhost-recon`, or `ad-kerberos-enum`.
- **`.env`/SSH keys/hashes** -> pivot to `secrets-vcs-config-audit` or `crypto-hash-jwt-triage`.

## Timeout & False-Positive Guards
- Use `sudo -ln` (non-interactive); wrap `pspy` in `timeout 45s` to prevent hangs.
- Filter stock SUIDs (`su`, `sudo`, `passwd`, `mount`, `ping`) before reporting.
- Check `ss -tulnp` before binding ports; verify cron/service binary write-permissions directly.

## Severity & Evidence Criteria
- **Critical**: `sudo` `(ALL) NOPASSWD`, writable root cron/service binary, `SeImpersonate`/`SeDebug` exploit path, unquoted writable service.
- **High**: Exploitable SUID/capability (`cap_setuid`), stored `cmdkey` admin creds, local unauthenticated Docker/DB socket.
- **Medium**: Readable backup/config with low-priv creds, non-standard SUID without direct escalation path.
- **Info**: OS/kernel version, listening port map, baseline privilege.
- **Redaction**: Mask passwords, SSH keys, SAM/shadow hashes to `<prefix>...<last4>`.
