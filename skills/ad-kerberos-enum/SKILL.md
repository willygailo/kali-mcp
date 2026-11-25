---
name: ad-kerberos-enum
description: Enumerate Active Directory, SMB, Kerberos, LDAP, and ADCS surfaces in read-only mode. Use when ports 88, 135, 139, 389, 445, 636, 3268, or 5985 are open or AD/SMB/Kerberos/WinRM appear.
category: infrastructure
triggers:
  ports: [88, 135, 139, 389, 445, 636, 3268, 5985]
  services: [smb, microsoft-ds, kerberos, ldap, ldaps, winrm]
  keywords: [smb, active directory, kerberos, ldap, bloodhound, domain controller, adcs, winrm]
recommended_tools: [enum4linux_ng, execute_command]
allowed_mode: read_only
---

# AD & Kerberos Read-Only Enumeration

## Trigger & Scope
- Activate on DC/SMB/LDAP/WinRM ports (`88, 135, 139, 389, 445, 636, 3268, 5985`) or `.htb`/`.local` domain banners.
- Verify `/etc/hosts` maps `<DC_IP> <dc.domain.local> <domain.local>` so Kerberos SPNs resolve cleanly.
- Verified binaries only: `nxc`, `netexec`, `enum4linux-ng`, `ldapsearch`, `rpcclient`, `smbmap`, `kerbrute`, `impacket-GetUserSPNs`, `impacket-GetNPUsers`, `impacket-lookupsid`, `impacket-findDelegation`, `bloodhound-python`, `certipy-ad`, `bloodyad`, `evil-winrm`.

## Step 1: SMB, NetBIOS & Anonymous Discovery
- Host/signing/SMB version and guest/null checks:
  - `enum4linux_ng` tool or `enum4linux-ng -A <IP>`
  - `nxc smb <IP> --shares -u '' -p ''` (or `-u 'guest' -p ''`)
  - `smbmap -H <IP> -u '' -p ''`
  - `rpcclient -U "" -N <IP> -c "enumdomusers;enumdomgroups;getdompwinfo"`
- Inspect readable non-default shares (`SYSVOL`, `NETLOGON`, `Docs`, `Backups`) read-only; look for GPP XML, scripts, or user lists.

## Step 2: LDAP / LDAPS Read-Only Queries
- Base naming context & rootDSE (unauthenticated or with discovered creds):
  - `ldapsearch -x -H ldap://<IP> -s base namingContexts`
  - `ldapsearch -x -H ldap://<IP> -b "DC=domain,DC=local" "(objectClass=user)" sAMAccountName description servicePrincipalName`
- Check `description`, `info`, `userAccountControl`, and password-policy attributes before any credentialed step.

## Step 3: Kerberos User, AS-REP & SPN Triage
- Valid username discovery (non-locking, no password guessing):
  - `kerbrute userenum -d <domain> --dc <IP> /usr/share/seclists/Usernames/xato-net-10-million-usernames.txt`
- AS-REP Roastable accounts (pre-auth disabled):
  - `impacket-GetNPUsers <domain>/ -usersfile users.txt -no-pass -dc-ip <IP>`
- Kerberoastable SPNs (once a low-priv domain account is known):
  - `impacket-GetUserSPNs <domain>/<user>:<pass> -dc-ip <IP> -request`
- RID cycling & delegation audit:
  - `impacket-lookupsid <domain>/<user>:<pass>@<IP>`
  - `impacket-findDelegation <domain>/<user>:<pass> -dc-ip <IP>`

## Step 4: BloodHound, ADCS & ACL Mapping (Read-Only)
- Collect AD graph for offline path analysis:
  - `bloodhound-python -u <user> -p <pass> -d <domain> -ns <IP> -c all`
- Inspect ADCS templates & CA misconfigurations (`ESC1`-`ESC13` discovery):
  - `certipy-ad find -u <user>@<domain> -p <pass> -dc-ip <IP> -vulnerable -stdout`
- Query ACLs/object attributes without modifying AD objects:
  - `bloodyad -u <user> -p <pass> -d <domain> --host <DC_FQDN> get object <target_dn>`
- Validate WinRM access read-only (`id; whoami /all` check only when authorized creds exist):
  - `nxc winrm <IP> -u <user> -p <pass>`
  - `evil-winrm -i <IP> -u <user> -p <pass>`

## Pivots & Guardrails
- If `$krb5asrep$` or `$krb5tgs$` hashes are returned, hand off to `crypto-hash-jwt-triage`.
- Never run password-spraying, `secretsdump`, DCSync, or ACL/template writes without explicit operator approval.
- Redact NTLM hashes, Kerberos tickets, and passwords in final summaries.
