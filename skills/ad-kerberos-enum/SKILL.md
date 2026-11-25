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

## Scope & Host Guards
- Map `<DC_IP> <dc.domain.local>` in `/etc/hosts` for Kerberos SPN resolution.
- Tools: `nxc`, `enum4linux-ng`, `ldapsearch`, `rpcclient`, `smbmap`, `kerbrute`, `impacket-Get{UserSPNs,NPUsers,lookupsid,findDelegation}`, `bloodhound-python`, `certipy-ad`, `bloodyad`, `evil-winrm`.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.
- No spraying, DCSync, `secretsdump`, or ACL/ADCS writes.

## Tactical Decision Tree
- **SMB (445)** -> `enum4linux_ng` + `timeout 30s nxc smb <IP> --shares -u '' -p ''`; shares readable -> `timeout 30s smbmap -H <IP> -u '' -p ''`; GPP/creds -> `secrets-vcs-config-audit`
- **RPC null** -> `timeout 25s rpcclient -U "" -N <IP> -c "enumdomusers;enumdomgroups;getdompwinfo"`
- **LDAP (389/636)** -> `timeout 25s ldapsearch -x -H ldap://<IP> -s base namingContexts`; `timeout 30s ldapsearch -x -H ldap://<IP> -b "DC=dom,DC=local" "(objectClass=user)" sAMAccountName description`
- **Kerberos (88) + users** -> `timeout 60s kerbrute userenum -d <dom> --dc <IP> /usr/share/seclists/Usernames/Names/names.txt`; `timeout 30s impacket-GetNPUsers <dom>/ -usersfile /tmp/users.txt -no-pass -dc-ip <IP>`
- **Domain creds** -> `timeout 45s impacket-GetUserSPNs <dom>/<u>:<p> -dc-ip <IP> -request`; `timeout 90s bloodhound-python -u <u> -p <p> -d <dom> -ns <IP> -c all`; `timeout 60s certipy-ad find -u <u>@<dom> -p <p> -dc-ip <IP> -vulnerable -stdout`
- **`$krb5asrep$`/`$krb5tgs$`** -> pivot to `crypto-hash-jwt-triage`
- **WinRM (5985) + creds** -> `timeout 20s nxc winrm <IP> -u <u> -p <p>` -> `privesc-pivoting-transfer`

## Timeout & False-Positive Guards
- Use `Names/names.txt` (~10k) before `xato-net-10-million`; check lockout via `getdompwinfo`.
- Enforce `-N`, `-no-pass`, `-Pn`, and `timeout 20s-90s`; ignore `IPC$`/`ADMIN$` noise.
- Clock skew -> verify time before treating `KRB_AP_ERR_SKEW` as bad account.

## Severity & Evidence Criteria
- **Critical**: Writable `SYSVOL`, privileged AS-REP/Kerberoastable SPN, ESC1-ESC8, unconstrained non-DC delegation.
- **High**: SMB signing off + relayable, shares with creds/GPP, Tier-0 ACL write path.
- **Medium**: Null SMB/LDAP user dump, weak `minPwdLength < 8` or no lockout.
- **Info**: Naming context, DC hostname/OS, default share list.
- **Redact**: Mask `$krb5*`, NTLM hashes, passwords to `<prefix>...<last4>`.
