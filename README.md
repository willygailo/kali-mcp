<p align="center">
  <img src="assets/banner.png" alt="Kali MCP AI Workbench Banner" width="100%" />
</p>

<h1 align="center">🐉 Kali MCP AI Workbench</h1>

<p align="center">
  <strong>🎯 Target &amp; 9 Lab/CTF Presets</strong> &nbsp;•&nbsp;
  <strong>🧭 6 Multi-Step Recon Playbooks</strong> &nbsp;•&nbsp;
  <strong>🧩 8 Modular Domain Skills</strong> &nbsp;•&nbsp;
  <strong>⚡ 18 Direct Tools + Local MCP Bridge</strong> &nbsp;•&nbsp;
  <strong>🤖 Multi-Provider LLMs</strong>
</p>

> **AI-powered Authorized Lab, CTF &amp; HTB Recon &amp; Security Assessment Workbench** for **Kali Linux** (`kali-server-mcp`) — featuring a dedicated **PySide6 Desktop GUI** (side-by-side layout), an **Interactive &amp; Playbook-Capable Terminal Agent**, **secret-redacting structured parsers**, **deduplicating SQLite workspaces**, and **categorized HTML/Markdown reporting** with multi-provider LLM support (**ChatGPT / OpenAI**, **Google Gemini**, **Anthropic Claude**, **xAI Grok**, **NVIDIA NIM**, and **Custom / Local** OpenAI-compatible endpoints).

<p align="center">
  <img src="https://img.shields.io/badge/Kali-Linux-557C94?style=flat-square&logo=kalilinux&logoColor=white" alt="Kali Linux" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PySide6" />
  <img src="https://img.shields.io/badge/LLM-OpenAI%20%7C%20Gemini%20%7C%20Claude%20%7C%20Grok%20%7C%20NIM-76B900?style=flat-square" alt="LLM Providers" />
  <a href="https://github.com/willygailo/kali-mcp/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/willygailo/kali-mcp?style=flat-square&color=58a6ff" alt="Contributors" />
  </a>
  <a href="https://github.com/willygailo/kali-mcp/commits/main">
    <img src="https://img.shields.io/github/last-commit/willygailo/kali-mcp?style=flat-square&color=3fb950" alt="Last Commit" />
  </a>
</p>

---

## 🖼️ Desktop GUI Preview

<p align="center">
  <img src="assets/gui-preview.png" alt="Kali MCP AI Workbench Desktop GUI" width="100%" />
</p>

---

## ✨ Features

- **Multi-Provider LLM Support:** Switch seamlessly between **ChatGPT / OpenAI**, **Google Gemini**, **Anthropic Claude**, **xAI Grok**, **NVIDIA NIM**, and **Custom / Local** OpenAI-compatible servers (Ollama, vLLM, LM Studio) with automatic key-prefix detection, live connection testing, and context-safe tool output trimming (`trim_tool_output_for_llm`).
- **6 Built-in Lab / CTF / HTB Recon Playbooks:** Run end-to-end automated multi-step pipelines from either the Desktop GUI (`playbook_combo`) or CLI (`--run-playbook`, `/run`):
  1. `endpoint_api_hunter` — **Endpoint, JS &amp; API Hunter** (`httpx-toolkit` + `whatweb` → `katana` + spec probe → `ffuf` API/GraphQL fuzz → `arjun` hidden parameters)
  2. `domain_origin_vhost` — **Domain, Real IP / Origin &amp; VHost Recon** (`dig` + `whois` + `openssl` CN/SAN → `wafw00f` + `httpx-toolkit` → `subfinder` → `ffuf` VHost auto-calibration)
  3. `secret_config_audit` — **Exposed Secrets, Keys &amp; Config Audit** (read-only `.env`/`.git`/config probe → landing HTML &amp; in-scope JS bundle audit → `ffuf` quickhits)
  4. `full_htb_ctf_recon` — **Full HTB / Lab Box Recon** (fast TCP top-1000 → `-sCV` service/scripts → web/TLS/DNS/WhatWeb → `enum4linux-ng` SMB/AD → `searchsploit`)
  5. `web_recon` — **Web Recon Pipeline** (Nmap web ports → TLS &amp; HTTP headers → Gobuster dir → Nikto)
  6. `network_audit` — **Network Audit Pipeline** (fast TCP discovery → `-sCV` service/scripts → SMB / Enum4linux)
- **GUI Audit Prompt &amp; Playbook Loader (`prompts/prompt.txt`):** Auto-discovers `prompts/prompt.txt` / `prompts/prompt*.txt` / `playbooks/*`, lets you load custom methodology files, or open **Configure / Edit** (`PromptPlaybookDialog`) to edit instructions and fill optional `Target`, `Scope`, and `Time budget (easy | medium | hard)` context fields synced into the live AI system prompt.
- **Modular Lab / CTF / HTB Domain Skills (`skills/*/SKILL.md`):** Ships **8 built-in read-only domain skill packs** with progressive disclosure (compact Tier-1 index in `SYSTEM_PROMPT`, Tier-2 bodies capped at `MAX_ACTIVE_SKILLS = 3`, `MAX_SKILL_BODY_CHARS = 2400`, `MAX_SKILLS_CHARS = 6000`), GUI Domain Skills bar/chips (`SkillSelectorDialog`, finding-based auto-suggestions, per-engagement SQLite persistence), CLI flags &amp; slash commands, optional `cve-mcp`/`ghidra-mcp` local stdio bridge (`app/kali_mcp_bridge.py`), and an Antigravity skill export (`integrations/antigravity/kali-mcp-workbench/SKILL.md`).
- **Categorized Findings, Redacted Secrets &amp; Deduplicated SQLite Store:**
  - Automatically parses outputs into 7 structured categories (`secret`, `vulnerability`, `misconfig`, `endpoint`, `asset`, `service`, `exploit`) with entropy &amp; false-positive filtering (SRI hashes, webpack chunks, data URIs, placeholders, UUIDs, Stripe `pk_`).
  - **Mandatory Secret Redaction:** Raw credentials are always masked (`redact_secret`) before entering `Finding.title`, `Finding.details`, `Finding.evidence`, SQLite storage, GUI tables, or reports.
  - **7-Column Findings &amp; Assets Table + Details Pane:** Filter by keyword, category, and severity, inspect full details &amp; redacted evidence with one-click **Copy Evidence**, and trigger **⚡ Follow-Up** scans without overwriting your engagement's primary target.
  - **Non-Destructive SQLite Migration &amp; Deduplication:** Existing databases automatically add `category` and `evidence` columns without data loss, and repeated scans update matching findings in place instead of creating duplicates.
- **Categorized HTML &amp; Markdown Engagement Reports:** Export dark/print-friendly HTML or escaped Markdown writeups featuring an **Executive Summary** (Severity + Category counts), 5 structured finding sections (Redacted Secrets, Assets/Subdomains/VHosts/Origin IPs, Endpoints/APIs/Params, Vulnerabilities &amp; Misconfigurations, Open Ports/Services &amp; Exploits), Lab/CTF notes, AI analysis (with automatic fallback to persisted scan analysis), and raw scan evidence.

---

## 📁 Project Structure

| File | Description |
| :--- | :--- |
| `app/kali-gui.py` | PySide6 Desktop GUI (`KaliGuiWindow`) entrypoint with streaming AI, playbooks, audit prompt loader, categorized findings, and reports |
| `app/kali_gui_*.py` | Modular Desktop GUI components (theme, per-run workers, API keys, `PromptPlaybookDialog` &amp; `SkillSelectorDialog`, skills bar mixin, UI layout, actions) |
| `app/kali-agent.py` | Interactive &amp; CLI playbook/skill runner (`--list-playbooks`, `--run-playbook`, `--ai-triage`, `--list-skills`, `--skill`, `--auto-skills`, `/playbooks`, `/run`, `/playbook`, `/skills`, `/skill`, `/tools`) |
| `app/kali_core.py` &amp; `app/kali_core_*.py` | Shared core + helper modules (`builders`, `playbooks`, `providers`): target normalizer, `shell=False`-safe command builder, prompt loader, 6 `PLAYBOOKS`, 18 `DIRECT_TOOLS`, 9 `QUICK_PRESETS`, LLM trimming, and streaming agent loop |
| `app/kali_skills.py` &amp; `app/kali_mcp_bridge.py` | Zero-dependency `SKILL.md` progressive loader/matcher + optional capability-gated `cve-mcp` / `ghidra-mcp` local stdio MCP bridge |
| `skills/*/SKILL.md` | 8 built-in read-only Lab / CTF / HTB domain skill modules (AD/Kerberos, Binary/RE, Crypto/JWT, Forensics, Infra/DB, PrivEsc/Pivot, Secrets/VCS, Web/API) |
| `integrations/antigravity/kali-mcp-workbench/SKILL.md` | Reusable Antigravity agent skill export for orchestrating Kali MCP Workbench CLI/GUI and safety rules |
| `app/kali_parsers.py` &amp; `app/kali_parsers_*.py` | Structured parsers + helper modules (`dns`, `secrets`, `web`): DNS/WHOIS/TLS/WAF, subdomains/vhosts, endpoints/params, redacted secrets, enum4linux, nmap, gobuster/dirb, nikto, sqlmap, wpscan, searchsploit |
| `app/kali_store.py` | SQLite persistence with non-destructive schema migration (`category`, `evidence`, `active_skills_json`), finding deduplication, and category counts |
| `app/kali_reports.py` | Categorized standalone HTML and Markdown engagement/CTF writeup report generator |
| `tests/test_kali_workbench.py` | Deterministic offline `pytest` unit &amp; headless GUI smoke test suite (`24` tests) |
| `app/pyarmor_runtime_000000/` | PyArmor runtime library required by the `20` obfuscated `app/` Python modules |
| `scripts/build-obfuscated.sh` | Maintainer build script to regenerate protected `app/*.py` modules from local `src_private/` |
| `run-gui.sh` / `run-agent.sh` | One-command launchers with automatic Python 3 dependency resolution (`resolve_python`) that ensure `kali-server-mcp` is running |
| `scripts/kali-mcp-manager.sh` | Control script for `/usr/bin/kali-server-mcp` (`start`, `stop`, `restart`, `status`) |
| `prompts/prompt.txt` | Default audit prompt / methodology file auto-discovered by the GUI and CLI |
| `.env.example` | Template for provider API keys (`NVIDIA_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, `CUSTOM_*`) |
| `CONTRIBUTING.md` | Contribution workflow and verification guidelines |

---

## ⚙️ Setup &amp; Installation

### 1. Prerequisites
- Kali Linux with **`kali-server-mcp`** installed (`/usr/bin/kali-server-mcp`) and standard recon CLI tools (`nmap`, `ffuf`, `gobuster`, `dirb`, `nikto`, `sqlmap`, `wpscan`, `whatweb`, `wafw00f`, `httpx-toolkit`, `katana`, `subfinder`, `arjun`, `enum4linux-ng`, `dig`, `whois`, `openssl`, `searchsploit`) + SecLists.
- Python 3 packages: `openai`, `requests`, `PySide6`, `rich`, `pytest`, and `mcp` (optional, for local `cve-mcp` / `ghidra-mcp` stdio bridge).

```bash
pip install openai requests PySide6 rich pytest mcp
```

### 2. Configure API Keys (`.env`)
Copy `.env.example` to `.env` or configure credentials inside the Desktop GUI via **`🔑 API Keys`**:

```bash
cp .env.example .env
```

```env
# ChatGPT / OpenAI
OPENAI_API_KEY="sk-your-openai-api-key"

# Google Gemini
GEMINI_API_KEY="AIza-your-gemini-api-key"

# Anthropic Claude
ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key"

# xAI Grok
XAI_API_KEY="xai-your-xai-api-key"

# NVIDIA NIM
NVIDIA_API_KEY="nvapi-your-nvidia-api-key"

# Custom / Local OpenAI-compatible endpoint (Ollama, vLLM, LM Studio, etc.)
# CUSTOM_BASE_URL="http://127.0.0.1:11434/v1"
# CUSTOM_MODEL="llama3.2"
```

---

## 🚀 Usage

### 🖥️ Desktop GUI (Recommended)
```bash
./run-gui.sh
```
*(Supports `./run-gui.sh --help` and headless verification via `QT_QPA_PLATFORM=offscreen ./run-gui.sh --smoke-test`.)*
1. Click **`🔑 API Keys`** in the top bar to add, test, and save provider credentials to `.env`.
2. Enter your **Target** (`IP`, `domain`, or `URL[:port]`) in the left pane.
3. Choose one of the **9 Quick Presets**, run any of the **6 Automated Recon Playbooks**, or pick any of the **18 Core Direct Tools** (+ optional `cve_lookup` / `ghidra_triage` when `cve-mcp`/`ghidra-mcp` are installed).
4. Optionally select `prompts/prompt.txt` (or click **Load...** / **Configure / Edit** for `PromptPlaybookDialog`) in the **Audit Prompt / System Playbook** bar, and toggle up to 3 domain skill packs in the **Domain Skills** bar/chips (**Skills...** opens `SkillSelectorDialog`, and auto-suggested chips appear from discovered ports/services/keywords).
5. Inspect live raw output + streaming AI analysis side-by-side in **Tab 1**, filter/copy redacted evidence &amp; trigger follow-ups in **Tab 2 (Findings &amp; Assets)**, and export categorized HTML or Markdown reports in **Tab 3**.

### 💻 Terminal CLI Agent &amp; Playbook Runner
- **List all 6 built-in recon playbooks or 8 modular domain skills (works offline, no API key needed):**
  ```bash
  ./app/kali-agent.py --list-playbooks
  ./app/kali-agent.py --list-skills
  ```
- **Run a multi-step recon playbook directly from the CLI (with optional skill selection / auto-matching):**
  ```bash
  ./app/kali-agent.py --run-playbook endpoint_api_hunter --target https://lab.target.local
  ./app/kali-agent.py --run-playbook full_htb_ctf_recon --target 10.10.10.5 --ports 22,80,445 --ai-triage --auto-skills
  ```
- **Interactive AI chat with slash commands (`/playbooks`, `/run`, `/playbook`, `/skills`, `/skill`, `/tools`, `/help`):**
  ```bash
  ./run-agent.sh
  ./run-agent.sh --playbook prompts/prompt.txt --skill ad-kerberos-enum --skill web-api-vhost-recon
  ./run-agent.sh --playbook prompts/prompt.txt --auto-skills "Audit 10.10.10.5"
  ```

<details>
<summary>All CLI Options &amp; Interactive Slash Commands for <code>app/kali-agent.py</code></summary>

| Flag / Command | Description |
| :--- | :--- |
| `--list-playbooks` | Print all 6 built-in multi-step recon playbooks and exit (offline) |
| `--list-skills` | Print all discovered domain skills (`name`, `category`, `allowed_mode`, `description`, `triggers`) and exit (offline) |
| `--skill NAME` | Activate a domain skill by name (repeatable, up to `MAX_ACTIVE_SKILLS = 3`) |
| `--auto-skills` | Automatically select top matching skills from target, prompt, or playbook findings |
| `--run-playbook KEY` | Run a built-in recon pipeline directly against `--target` |
| `--target TARGET` | Target IP, domain, or URL for `--run-playbook` |
| `--wordlist PATH` | Override wordlist path for fuzzing steps |
| `--ports PORTS` | Custom ports (e.g., `80,443` or `1-1000`) |
| `--extra-args FLAGS` | Extra flags passed to playbook tools |
| `--ai-triage` | Feed `--run-playbook` parsed findings to the LLM for prioritized triage |
| `--playbook FILE` | Load a custom audit prompt/playbook file (e.g., `prompts/prompt.txt`) |
| `--provider` / `--model` / `--api-key` / `--base-url` | Select or override LLM provider configuration |
| `--yes`, `-y` | Auto-approve tool calls without confirmation prompts |
| `/playbooks` | *(In-chat)* List all 6 built-in recon pipelines |
| `/run <key> <target>` | *(In-chat)* Execute a recon pipeline and inject findings into AI context |
| `/playbook <file\|off>` | *(In-chat)* Load or clear custom audit prompt file |
| `/skills` | *(In-chat)* List all domain skills and mark currently active ones |
| `/skill <name\|auto\|off\|list>` | *(In-chat)* Toggle a skill, auto-detect from context/findings, clear active skills, or list skills |
| `/tools` | *(In-chat)* List all 18 direct tools and MCP function tools |
| `/help` | *(In-chat)* Show slash command reference |

</details>

---

## 🧩 Modular Lab / CTF / HTB Domain Skills (`skills/*/SKILL.md`)

Domain skills extend `prompts/prompt.txt` with specialized, read-only methodology without bloating the LLM context window:

| Skill | Category | Primary Triggers &amp; Scope | Mode |
| :--- | :--- | :--- | :--- |
| `ad-kerberos-enum` | `infrastructure` | Ports `88, 135, 139, 389, 445, 636, 3268, 5985`; SMB, Kerberos, LDAP, WinRM, ADCS | `read_only` |
| `binary-re-pwn-triage` | `binary` | ELF/PE/APK static &amp; dynamic triage (`readelf`, `gdb/gef`, `ropper`, `r2`, `ghidra_triage`, `frida`) | `read_only` |
| `crypto-hash-jwt-triage` | `crypto` | `hashid`, John/Hashcat offline modes, Base64/JWT (`eyJ...`) header &amp; claim inspection | `read_only` |
| `forensics-pcap-steg-triage` | `forensics` | PCAP/PCAPNG (`tshark`), Volatility 3 memory dumps, EXIF/binwalk/steg, PDF/Office macros | `read_only` |
| `infra-db-services-enum` | `infrastructure` | Ports `21, 22, 53, 111, 161, 2049, 2375, 3306, 5432, 6379, 9200, 11211, 27017` + `cve_lookup` | `read_only` |
| `privesc-pivoting-transfer` | `privesc` | Linux/Windows post-foothold enum (`linpeas`, `winpeas`, `pspy`), `ligolo-proxy`/`chisel` | `read_only` |
| `secrets-vcs-config-audit` | `secrets` | `.env`, `.git`, `.js.map`, `secret_exposure_scan`, `gitleaks`, `trufflehog`, mandatory redaction | `read_only` |
| `web-api-vhost-recon` | `web` | Ports `80, 443, 3000, 5000, 8000, 8080, 8443, 9000`; `httpx-toolkit`, VHost fuzzing, APIs/GraphQL | `read_only` |

- **Progressive Disclosure &amp; Token Caps:** `app/kali_skills.py` injects only a compact Tier-1 catalog (`render_skill_index`) into `SYSTEM_PROMPT`. Tier-2 tactical instructions (`render_active_skills_block`) load only for active skills, capped at `MAX_ACTIVE_SKILLS = 3`, `MAX_SKILL_BODY_CHARS = 2400` per skill, and `MAX_SKILLS_CHARS = 6000` total.
- **Local Overrides &amp; Authoring:** Add custom skills under `~/.local/share/kali-mcp/skills/<name>/SKILL.md` or `KALI_MCP_SKILLS_DIR` (plus gitignored `skills/*.local/` and `skills/.cache/`) using YAML frontmatter (`name`, `description`, `category`, `triggers: {ports, services, keywords}`, `recommended_tools`, `allowed_mode: read_only`).
- **Optional Local MCP Bridge (`cve-mcp` &amp; `ghidra-mcp`):** `app/kali_mcp_bridge.py` detects `cve-mcp` and `ghidra-mcp` on `PATH` and exposes read-only `cve_lookup` and `ghidra_triage` tools to both the LLM and GUI/CLI without requiring `kali-server-mcp`.
- **Antigravity Skill Export:** Copy or link `integrations/antigravity/kali-mcp-workbench/SKILL.md` to `~/.agents/skills/kali-mcp-workbench/SKILL.md` to invoke Kali MCP Workbench workflows directly from Antigravity.

---

## 🛠️ Direct &amp; Composite Recon Tools (`18` Core + `2` Optional Local MCP)

| Tool Key | Display Name | Mode / Engine |
| :--- | :--- | :--- |
| `nmap_scan` | Nmap Port &amp; Service Scan | `/api/tools/nmap` |
| `gobuster_scan` | Gobuster Directory / Web | `/api/tools/gobuster` |
| `dirb_scan` | Dirb Web Content Scan | `/api/tools/dirb` |
| `nikto_scan` | Nikto Web Vulnerability Scan | `/api/tools/nikto` |
| `sqlmap_scan` | SQLmap Injection Test | `/api/tools/sqlmap` |
| `wpscan_analyze` | WPScan WordPress Audit | `/api/tools/wpscan` |
| `enum4linux_scan` | Enum4linux SMB Enum | `/api/tools/enum4linux` |
| `enum4linux_ng` | Enum4linux-ng SMB / AD Audit | `/api/command` (`enum4linux-ng` / fallback `enum4linux`) |
| `origin_dns_tls` | Origin, DNS, WHOIS &amp; TLS Recon | `/api/command` (`dig`, `whois`, `openssl`, `curl`) |
| `tech_waf_fingerprint` | Tech &amp; WAF Fingerprint | `/api/command` (`wafw00f`, `httpx-toolkit`, `whatweb`, `curl`) |
| `subdomain_enum` | Subdomain Enum (`subfinder`) | `/api/command` (`subfinder -silent`) |
| `vhost_fuzz` | Virtual Host Fuzz (`ffuf`) | `/api/command` (`ffuf -ac` + SecLists DNS) |
| `endpoint_crawl` | Endpoint, JS &amp; API Crawl | `/api/command` (`katana`, `ffuf`, well-known spec probe) |
| `param_discover` | Hidden Param Discovery (`arjun`) | `/api/command` (`arjun -t 5 --stable`) |
| `secret_exposure_scan` | Secret &amp; Config Exposure Audit | `/api/command` (read-only config/VCS &amp; HTML/JS audit, redacted) |
| `tls_dns` | TLS &amp; DNS Quick Check | `/api/command` (`openssl s_client`, `curl`, `dig`) |
| `searchsploit` | Searchsploit Exploit-DB Lookup | `/api/command` (`searchsploit --json`) |
| `execute_command` | Raw Shell Command | `/api/command` (`bash -c`) |
| `cve_lookup` | CVE Lookup (`cve-mcp`, optional) | Local stdio MCP (`app/kali_mcp_bridge.py`) |
| `ghidra_triage` | Ghidra Headless Binary Triage (`ghidra-mcp`, optional) | Local stdio MCP (`app/kali_mcp_bridge.py`) |

Additional MCP endpoints available to the AI agent: `hydra_attack`, `john_crack`, and `metasploit_run`.

---

## 🧪 Automated Testing &amp; Linting

Run the offline unit &amp; headless GUI smoke test suite and linter (no network access or API keys required):

```bash
ruff check src_private tests
PYTHONPATH=src_private pytest -v tests/test_kali_workbench.py
QT_QPA_PLATFORM=offscreen KALI_MCP_DB_PATH=/tmp/kali-mcp-smoke.db ./run-gui.sh --smoke-test
```

---

## 🛑 Managing the Kali API Server

`kali-server-mcp` listens on `http://127.0.0.1:5000` (logs at `/tmp/kali-server-mcp.log`):

```bash
./scripts/kali-mcp-manager.sh status   # Check if running and healthy
./scripts/kali-mcp-manager.sh start    # Start the background server
./scripts/kali-mcp-manager.sh restart  # Restart the server
./scripts/kali-mcp-manager.sh stop     # Stop the server
```

---

## 🔒 Code Protection (PyArmor)

All **20** distributed `.py` modules in `app/` are protected with **PyArmor 9.3.0** targeting **Linux x86_64 / Python 3.14** and require the bundled `app/pyarmor_runtime_000000/` directory at runtime.

Maintainers keep editable source modules in the local, gitignored `src_private/` directory and regenerate the protected `app/*.py` files (with a **`28 KB` / `28,672`-byte pre-PyArmor per-file size guard** and built-in leak verification) via:

```bash
./scripts/build-obfuscated.sh
```

---

## 🔧 Troubleshooting

- **`ModuleNotFoundError: No module named 'PySide6.QtCore'`:** On Kali/Debian, `apt autoremove` can remove Qt bindings while leaving `libpyside6-py3-*`. Both `run-gui.sh` (via `resolve_python`) and `app/kali-gui.py` check for working Qt modules and print the exact fix:
  ```bash
  sudo apt install -y python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets
  # Or install into user site-packages:
  /usr/bin/python3 -m pip install --user --break-system-packages PySide6-Essentials openai requests rich
  ```
- **`kali-server-mcp` Offline:** Run `./scripts/kali-mcp-manager.sh restart` and inspect `/tmp/kali-server-mcp.log`.
- **Missing API Key Error:** Ensure a `.env` file exists in the project root (see `.env.example`), export the matching provider variable (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, or `NVIDIA_API_KEY`), or configure it via **`🔑 API Keys`** in the Desktop GUI.
- **Localhost Proxy Interference:** Automatically bypassed in `app/kali_core.py` (`http_session.trust_env = False`) and via `NO_PROXY=localhost,127.0.0.1` in the launcher scripts.
- **ProjectDiscovery `httpx` vs Python `httpx`:** Kali ships ProjectDiscovery's HTTP prober as `/usr/bin/httpx-toolkit`; all built-in playbooks automatically invoke `httpx-toolkit`.
- **IDE Import Warnings (`kali_core` / `PySide6`):** Point your editor's Python interpreter to `/usr/bin/python3` and set `search-path = ["src_private"]` in your local `pyrefly.toml` (gitignored) so static analysis inspects readable sources instead of obfuscated `app/` modules.

---

## 🗺️ Roadmap

- [x] Custom wordlist picker and advanced flags panel in the GUI
- [x] Categorized HTML &amp; Markdown session report export (Executive Summary, Redacted Secrets, Assets, Endpoints, Findings, AI Analysis)
- [x] Streaming token output for real-time AI responses + context-safe tool output trimming
- [x] Persistent SQLite lab/CTF workspaces with non-destructive migration &amp; finding deduplication
- [x] 6 multi-step Lab/CTF/HTB recon playbooks &amp; 18 direct tools across GUI and CLI
- [x] GUI Audit Prompt / Playbook loader (`prompts/prompt.txt` + Target/Scope/Time budget dialog)
- [x] Offline `pytest` unit &amp; headless PySide6 GUI smoke test suite
- [x] Modular Lab/CTF/HTB Domain Skills (`skills/*/SKILL.md`), progressive prompt loader, and optional `cve-mcp`/`ghidra-mcp` bridge
- [ ] Live chunked stdout streaming for long-running scans on `kali-server-mcp`

---

## 👥 Contributors

Thanks to everyone who has contributed to this project! View the live contribution graph on [GitHub Contributors](https://github.com/willygailo/kali-mcp/graphs/contributors).

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/willygailo">
        <img src="https://github.com/willygailo.png?size=100" width="100px;" alt="willygailo"/><br />
        <sub><b>willygailo</b></sub>
      </a><br />
      <sub>Creator &amp; Maintainer</sub>
    </td>
  </tr>
</table>

<a href="https://github.com/willygailo/kali-mcp/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=willygailo/kali-mcp" alt="Contributors Graph" />
</a>

> Want to contribute? Check out [CONTRIBUTING.md](CONTRIBUTING.md) and open a Pull Request!

---

## ⚠️ Responsible Use Notice
Use this tool strictly for **authorized penetration testing engagements, personal lab environments, or CTF challenges**.
