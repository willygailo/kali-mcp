<p align="center">
  <img src="assets/banner.png" alt="Kali MCP AI Workbench Banner" width="100%" />
</p>

<h1 align="center">🐉 Kali MCP AI Workbench</h1>

<p align="center">
  <strong>🎯 Target &amp; 9 Lab/CTF Presets</strong> &nbsp;•&nbsp;
  <strong>🧭 6 Multi-Step Recon Playbooks</strong> &nbsp;•&nbsp;
  <strong>⚡ 18 Direct &amp; Composite Tools</strong> &nbsp;•&nbsp;
  <strong>🔐 Redacted Secret Auditing</strong> &nbsp;•&nbsp;
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
- **GUI Audit Prompt &amp; Playbook Loader (`prompt.txt`):** Auto-discovers `prompt.txt` / `prompt*.txt` / `playbooks/*`, lets you load custom methodology files, or open **Configure / Edit** (`PromptPlaybookDialog`) to edit instructions and fill optional `Target`, `Scope`, and `Time budget (easy | medium | hard)` context fields synced into the live AI system prompt.
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
| `kali-gui.py` | PySide6 Desktop GUI (`KaliGuiWindow`) entrypoint with streaming AI, playbooks, audit prompt loader, categorized findings, and reports |
| `kali_gui_*.py` | Modular Desktop GUI components (theme, per-run workers, API keys &amp; prompt dialogs, UI layout, actions) |
| `kali-agent.py` | Interactive &amp; CLI playbook runner (`--list-playbooks`, `--run-playbook`, `--ai-triage`, `/playbooks`, `/run`, `/playbook`, `/tools`) |
| `kali_core.py` &amp; `kali_core_*.py` | Shared core + helper modules (`builders`, `playbooks`, `providers`): target normalizer, `shell=False`-safe command builder, prompt loader, 6 `PLAYBOOKS`, 18 `DIRECT_TOOLS`, 9 `QUICK_PRESETS`, LLM trimming, and streaming agent loop |
| `kali_parsers.py` &amp; `kali_parsers_*.py` | Structured parsers + helper modules (`dns`, `secrets`, `web`): DNS/WHOIS/TLS/WAF, subdomains/vhosts, endpoints/params, redacted secrets, enum4linux, nmap, gobuster/dirb, nikto, sqlmap, wpscan, searchsploit |
| `kali_store.py` | SQLite persistence with non-destructive schema migration, finding deduplication, and category counts |
| `kali_reports.py` | Categorized standalone HTML and Markdown engagement/CTF writeup report generator |
| `tests/test_kali_workbench.py` | Deterministic offline `pytest` unit &amp; headless GUI smoke test suite (21 tests) |
| `pyarmor_runtime_000000/` | PyArmor runtime library required by the 17 obfuscated root Python modules |
| `build-obfuscated.sh` | Maintainer build script to regenerate protected root `.py` modules from local `src_private/` |
| `run-gui.sh` / `run-agent.sh` | One-command launchers that ensure `kali-server-mcp` is running |
| `kali-mcp-manager.sh` | Control script for `/usr/bin/kali-server-mcp` (`start`, `stop`, `restart`, `status`) |
| `.env.example` | Template for provider API keys (`NVIDIA_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, `CUSTOM_*`) |
| `CONTRIBUTING.md` | Contribution workflow and verification guidelines |

---

## ⚙️ Setup &amp; Installation

### 1. Prerequisites
- Kali Linux with **`kali-server-mcp`** installed (`/usr/bin/kali-server-mcp`) and standard recon CLI tools (`nmap`, `ffuf`, `gobuster`, `dirb`, `nikto`, `sqlmap`, `wpscan`, `whatweb`, `wafw00f`, `httpx-toolkit`, `katana`, `subfinder`, `arjun`, `enum4linux-ng`, `dig`, `whois`, `openssl`, `searchsploit`) + SecLists.
- Python 3 packages: `openai`, `requests`, `PySide6`, `rich`, `pytest`.

```bash
pip install openai requests PySide6 rich pytest
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
1. Click **`🔑 API Keys`** in the top bar to add, test, and save provider credentials to `.env`.
2. Enter your **Target** (`IP`, `domain`, or `URL[:port]`) in the left pane.
3. Choose one of the **9 Quick Presets**, run any of the **6 Automated Recon Playbooks**, or pick any of the **18 Direct Tools**.
4. Optionally select `prompt.txt` (or click **Load...** / **Configure / Edit**) in the **Audit Prompt / System Playbook** bar to guide AI analysis with Target, Scope, and Time budget context.
5. Inspect live raw output + streaming AI analysis side-by-side in **Tab 1**, filter/copy redacted evidence &amp; trigger follow-ups in **Tab 2 (Findings &amp; Assets)**, and export categorized HTML or Markdown reports in **Tab 3**.

### 💻 Terminal CLI Agent &amp; Playbook Runner
- **List all 6 built-in recon playbooks (works offline, no API key needed):**
  ```bash
  ./kali-agent.py --list-playbooks
  ```
- **Run a multi-step recon playbook directly from the CLI:**
  ```bash
  ./kali-agent.py --run-playbook endpoint_api_hunter --target https://lab.target.local
  ./kali-agent.py --run-playbook full_htb_ctf_recon --target 10.10.10.5 --ports 22,80,445 --ai-triage
  ```
- **Interactive AI chat with slash commands (`/playbooks`, `/run`, `/playbook`, `/tools`, `/help`):**
  ```bash
  ./run-agent.sh
  ./run-agent.sh --playbook prompt.txt
  ./run-agent.sh -y "Perform initial recon on 10.10.10.5"
  ```

<details>
<summary>All CLI Options &amp; Interactive Slash Commands for <code>kali-agent.py</code></summary>

| Flag / Command | Description |
| :--- | :--- |
| `--list-playbooks` | Print all 6 built-in multi-step recon playbooks and exit (offline) |
| `--run-playbook KEY` | Run a built-in recon pipeline directly against `--target` |
| `--target TARGET` | Target IP, domain, or URL for `--run-playbook` |
| `--wordlist PATH` | Override wordlist path for fuzzing steps |
| `--ports PORTS` | Custom ports (e.g., `80,443` or `1-1000`) |
| `--extra-args FLAGS` | Extra flags passed to playbook tools |
| `--ai-triage` | Feed `--run-playbook` parsed findings to the LLM for prioritized triage |
| `--playbook FILE` | Load a custom audit prompt/playbook file (e.g., `prompt.txt`) |
| `--provider` / `--model` / `--api-key` / `--base-url` | Select or override LLM provider configuration |
| `--yes`, `-y` | Auto-approve tool calls without confirmation prompts |
| `/playbooks` | *(In-chat)* List all 6 built-in recon pipelines |
| `/run <key> <target>` | *(In-chat)* Execute a recon pipeline and inject findings into AI context |
| `/playbook <file\|off>` | *(In-chat)* Load or clear custom audit prompt file |
| `/tools` | *(In-chat)* List all 18 direct tools and 11 MCP function tools |
| `/help` | *(In-chat)* Show slash command reference |

</details>

---

## 🛠️ Direct &amp; Composite Recon Tools (18)

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

Additional MCP endpoints available to the AI agent: `hydra_attack`, `john_crack`, and `metasploit_run`.

---

## 🧪 Automated Testing &amp; Linting

Run the offline unit &amp; headless GUI smoke test suite and linter (no network access or API keys required):

```bash
ruff check src_private tests
PYTHONPATH=src_private pytest -v tests/test_kali_workbench.py
```

---

## 🛑 Managing the Kali API Server

`kali-server-mcp` listens on `http://127.0.0.1:5000` (logs at `/tmp/kali-server-mcp.log`):

```bash
./kali-mcp-manager.sh status   # Check if running and healthy
./kali-mcp-manager.sh start    # Start the background server
./kali-mcp-manager.sh restart  # Restart the server
./kali-mcp-manager.sh stop     # Stop the server
```

---

## 🔒 Code Protection (PyArmor)

All **17** distributed `.py` modules in the repository root are protected with **PyArmor 9.3.0** targeting **Linux x86_64 / Python 3.14** and require the bundled `pyarmor_runtime_000000/` directory at runtime.

Maintainers keep editable source modules in the local, gitignored `src_private/` directory and regenerate the protected root `.py` files (with built-in leak verification) via:

```bash
./build-obfuscated.sh
```

---

## 🔧 Troubleshooting

- **`kali-server-mcp` Offline:** Run `./kali-mcp-manager.sh restart` and inspect `/tmp/kali-server-mcp.log`.
- **Missing API Key Error:** Ensure a `.env` file exists in the project root (see `.env.example`), export the matching provider variable (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, or `NVIDIA_API_KEY`), or configure it via **`🔑 API Keys`** in the Desktop GUI.
- **Localhost Proxy Interference:** Automatically bypassed in `kali_core.py` (`http_session.trust_env = False`) and via `NO_PROXY=localhost,127.0.0.1` in the launcher scripts.
- **ProjectDiscovery `httpx` vs Python `httpx`:** Kali ships ProjectDiscovery's HTTP prober as `/usr/bin/httpx-toolkit`; all built-in playbooks automatically invoke `httpx-toolkit`.
- **IDE Import Warnings (`kali_core` / `PySide6`):** Point your editor's Python interpreter to `/usr/bin/python3` and set `search-path = ["src_private"]` in your local `pyrefly.toml` (gitignored) so static analysis inspects readable sources instead of obfuscated root modules.

---

## 🗺️ Roadmap

- [x] Custom wordlist picker and advanced flags panel in the GUI
- [x] Categorized HTML &amp; Markdown session report export (Executive Summary, Redacted Secrets, Assets, Endpoints, Findings, AI Analysis)
- [x] Streaming token output for real-time AI responses + context-safe tool output trimming
- [x] Persistent SQLite lab/CTF workspaces with non-destructive migration &amp; finding deduplication
- [x] 6 multi-step Lab/CTF/HTB recon playbooks &amp; 18 direct tools across GUI and CLI
- [x] GUI Audit Prompt / Playbook loader (`prompt.txt` + Target/Scope/Time budget dialog)
- [x] Offline `pytest` unit &amp; headless PySide6 GUI smoke test suite
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
