---
name: kali-mcp-workbench
description: Orchestrate authorized Kali Linux lab, CTF, and HTB reconnaissance via Kali MCP Workbench CLI, GUI, playbooks, and modular skills. Use when running authorized Kali Linux lab, CTF, or HTB reconnaissance via Kali MCP Workbench (kali-agent.py, kali-gui.py, or kali-server-mcp).
---

# Kali MCP Workbench Integration

Use the local Kali MCP Workbench (`/home/willygailo/Downloads/kali-mcp`) for structured, read-only reconnaissance, playbooks, and domain skill triage against authorized lab, CTF, and HTB targets.

## Quick Commands (CLI & Server Lifecycle)
Run from `/home/willygailo/Downloads/kali-mcp`:
- **Manage Kali MCP API server** (`127.0.0.1:5000`):
  - `./kali-mcp-manager.sh start|stop|restart|status`
- **List built-in playbooks and modular skills (offline, no API key needed)**:
  - `./kali-agent.py --list-playbooks`
  - `./kali-agent.py --list-skills`
- **Run a deterministic multi-step recon playbook**:
  - `./kali-agent.py --run-playbook <playbook_key> --target <IP_or_URL> [--ai-triage] [--yes]`
  - Available playbook keys: `full_htb_ctf_recon`, `domain_origin_vhost`, `endpoint_api_hunter`, `secret_config_audit`, `web_recon`, `network_audit`
- **Activate domain skills or load the core audit playbook**:
  - `./kali-agent.py --playbook prompt.txt --skill ad-kerberos-enum --skill web-api-vhost-recon`
  - `./kali-agent.py --playbook prompt.txt --auto-skills "Audit 10.10.10.x"`
  - Interactive slash commands inside `kali-agent.py`: `/playbooks`, `/skills`, `/skill <name|auto|off|list>`, `/run <playbook> <target>`, `/playbook <file|off>`, `/tools`
- **Wrapper launchers** (auto-load `.env`, set `NO_PROXY=localhost,127.0.0.1`, start `kali-server-mcp`):
  - `./run-agent.sh` (CLI agent) | `./run-gui.sh` (PySide6 desktop workbench `kali-gui.py`)

## Critical Kali Execution & Environment Rules
1. **`shell=False` / `bash -c` Rule**: `kali-server-mcp`'s `/api/command` (`execute_command`) runs with `shell=False`. Whenever a command uses pipes (`|`), chaining (`&&`, `;`), subshells, or redirects (`>`), wrap it explicitly as `bash -c "<command>"`.
2. **`httpx-toolkit` Rule**: Always invoke `httpx-toolkit` (`/usr/bin/httpx-toolkit`) for ProjectDiscovery HTTP probing. Never run bare `httpx` (which maps to Python's `httpx` CLI).
3. **Host-Specific Tool Availability**:
   - Use `certipy-ad`, `bloodyad`, `ligolo-proxy`/`ligolo-agent`, `pwncat`, `gef` (`checksec`), `ropper`, `hashid`, and Python stdlib JWT decoding.
   - Do not invoke absent binaries (`ssh-audit`, `mongosh`, `haiti`, `jwt_tool`, `zsteg`, standalone `checksec`, `pwntools`).

## Strict Read-Only & Secret-Redaction Rules
- **Authorized Scope Only**: Operate strictly on the user-specified authorized lab, CTF, or HTB target.
- **Read-Only by Default**: Never mutate target data, create accounts, upload payloads, brute-force credentials, or execute destructive checks without explicit user confirmation.
- **Mandatory Redaction**: Mask any discovered tokens, API keys, passwords, or hashes in output summaries (show prefix + last 4 characters only, or `****` for short values).
