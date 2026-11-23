<p align="center">
  <img src="assets/banner.png" alt="Kali MCP AI Workbench Banner" width="100%" />
</p>

<h1 align="center">🐉 Kali MCP AI Workbench</h1>

<p align="center">
  <strong>🎯 Target &amp; Presets</strong> &nbsp;•&nbsp;
  <strong>⚡ Direct &amp; AI Scans</strong> &nbsp;•&nbsp;
  <strong>🤖 Multi-Provider LLMs</strong> &nbsp;•&nbsp;
  <strong>📊 Side-by-Side Output</strong> &nbsp;•&nbsp;
  <strong>🛡️ Safe Tool Approval</strong>
</p>

> **AI-powered Offensive Security & Recon Assistant** for **Kali Linux** (`kali-server-mcp`) — featuring a dedicated **PySide6 Desktop GUI** (side-by-side layout) and an **Interactive Terminal Agent** with multi-provider LLM support (**ChatGPT / OpenAI**, **Google Gemini**, **Anthropic Claude**, **xAI Grok**, **NVIDIA NIM**, and **Custom / Local** OpenAI-compatible endpoints).

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

- **Multi-Provider LLM Support:** Switch seamlessly between **ChatGPT / OpenAI**, **Google Gemini**, **Anthropic Claude**, **xAI Grok**, **NVIDIA NIM**, and **Custom / Local** OpenAI-compatible servers (e.g., Ollama, vLLM, LM Studio) with automatic key-prefix detection and curated model presets.
- **Side-by-Side Desktop GUI (`kali-gui.py`):**
  - **Built-in `🔑 API Keys` Manager:** Configure, unmask/verify, live-test (`Test`), and securely save provider API keys directly to `.env` (`0600` permissions) from the top bar, alongside provider and editable model selectors.
  - **Project / Engagement Workspaces:** Switch between lab/CTF targets with persistent SQLite storage (`kali_store.py`) for scan history, findings, notes, and AI chat context.
  - **Left Pane (Controls):** Target input (`IP / Domain / URL`), 6 one-click presets, **Multi-Step Playbooks** (`Web Recon Pipeline`, `Network Audit Pipeline`), collapsible **Advanced Tool Options** (Ports, Extra Flags, Wordlist picker), Direct Tool runner, and live elapsed timer.
  - **Right Pane (Instant Results):** View **Raw Tool Output / Terminal Log** (top) and **Streaming AI Analysis & Findings** (bottom) side-by-side, plus a **Findings & Ports** table with severity filtering & follow-up triggers, and **Lab/CTF Notes + HTML/Markdown Report Export**.
  - **Safe Execution:** Toggleable **Auto-approve** mode or an inline **Approve / Decline** banner before running any tool, plus instant HTTP session cancellation on Stop.
- **Interactive Terminal Agent (`kali-agent.py`):** Streaming token output and `rich` markdown/panel formatting for headless or SSH workflows.
- **Dual Mode (AI + Direct):** Let the AI orchestrate and summarize (`▶ Run with AI`) or execute all 11 Kali MCP tools directly (`⚡ Direct Tool`) without an LLM roundtrip.
- **Automatic `.env` Loading:** API keys stay safely out of version control in `.env` (gitignored) and are loaded automatically by the launchers and `kali_core.py`.

---

## 📁 Project Structure

| File | Description |
| :--- | :--- |
| `kali-gui.py` | PySide6 Desktop GUI (`KaliGuiWindow`) with streaming AI, playbooks, findings table, and notes |
| `kali-agent.py` | Interactive and one-shot CLI AI assistant with streaming output and `rich` formatting |
| `kali_core.py` | Shared core: `.env` loader, provider config, all 11 `TOOL_DEFINITIONS`, `PLAYBOOKS`, `call_kali_api`, and streaming agent loop |
| `kali_parsers.py` | Structured output parsers (`nmap`, `gobuster`, `dirb`, `nikto`, `sqlmap`, `tls/dns`, `searchsploit`) |
| `kali_store.py` | SQLite persistence for engagements, scans, findings, notes, and chat contexts |
| `kali_reports.py` | Standalone HTML and Markdown engagement/CTF writeup report generator |
| `run-gui.sh` | One-command launcher that starts `kali-server-mcp` and opens the Desktop GUI |
| `run-agent.sh` | One-command launcher that starts `kali-server-mcp` and opens the Terminal Agent |
| `kali-mcp-manager.sh` | Control script for `/usr/bin/kali-server-mcp` (`start`, `stop`, `restart`, `status`) |
| `.env.example` | Template for provider API keys (`NVIDIA_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, `CUSTOM_*`) |
| `CONTRIBUTING.md` | Contribution workflow and verification guidelines |

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Kali Linux with **`kali-server-mcp`** installed (`/usr/bin/kali-server-mcp`)
- Python 3 packages: `openai`, `requests`, `PySide6` (for GUI), and `rich` (optional for CLI formatting)

```bash
pip install openai requests PySide6 rich
```

### 2. Configure API Keys (`.env`)
Copy `.env.example` to `.env` and add the API key(s) for any provider you want to use (or manage them directly inside the Desktop GUI via **`🔑 API Keys`**):

```bash
cp .env.example .env
```

```env
# ChatGPT / OpenAI
OPENAI_API_KEY="sk-your-openai-api-key"
# OPENAI_MODEL="gpt-4o"

# Google Gemini
GEMINI_API_KEY="AIza-your-gemini-api-key"
# GEMINI_MODEL="gemini-2.5-flash"

# Anthropic Claude
ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key"
# ANTHROPIC_MODEL="claude-sonnet-4-5"

# xAI Grok
XAI_API_KEY="xai-your-xai-api-key"
# XAI_MODEL="grok-3"

# NVIDIA NIM
NVIDIA_API_KEY="nvapi-your-nvidia-api-key"
# NVIDIA_MODEL="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

# Custom / Local OpenAI-compatible endpoint (Ollama, vLLM, LM Studio, etc.)
# CUSTOM_BASE_URL="http://127.0.0.1:11434/v1"
# CUSTOM_MODEL="llama3.2"
# CUSTOM_API_KEY="ollama"
```

---

## 🚀 Usage

### 🖥️ Desktop GUI (Recommended)
```bash
./run-gui.sh
```
1. Click **`🔑 API Keys`** in the top bar to add, test, and save your **ChatGPT / OpenAI**, **Google Gemini**, **Anthropic Claude**, **xAI Grok**, **NVIDIA NIM**, or **Custom / Local** credentials to `.env`.
2. Choose your **Provider** and **Model** from the top bar dropdowns (or type any custom model ID).
3. Enter your **Target** (`IP`, `domain`, or `URL`) in the left pane.
4. Pick a **Quick Preset** or type a custom prompt.
5. Click **`▶ Run with AI`** for automated scanning + AI analysis, or **`⚡ Direct Tool`** for immediate raw tool output.
6. Inspect **Raw Tool Output** and **AI Analysis** side-by-side in the right pane, and export results via `Save .txt` or `Save .md`.

### 💻 Terminal CLI Agent
- **Interactive chat (auto-detects configured provider from `.env`):**
  ```bash
  ./run-agent.sh
  ```
- **One-shot command:**
  ```bash
  ./run-agent.sh "Scan 127.0.0.1 for open ports with nmap"
  ```
- **Auto-approve tool calls (`-y` / `--yes`):**
  ```bash
  ./run-agent.sh -y "Check HTTP headers and open ports on 127.0.0.1"
  ```
- **Select a specific LLM provider:**
  ```bash
  ./run-agent.sh --provider openai --model gpt-4o
  ./run-agent.sh --provider gemini --model gemini-2.5-flash
  ./run-agent.sh --provider claude --model claude-sonnet-4-5
  ./run-agent.sh --provider grok --model grok-3
  ./run-agent.sh --provider nvidia
  ./run-agent.sh --provider custom --base-url http://127.0.0.1:11434/v1 --model llama3.2
  ```

<details>
<summary>All CLI Options for <code>kali-agent.py</code></summary>

| Flag | Description |
| :--- | :--- |
| `prompt` | Optional initial prompt for one-shot execution |
| `--provider {nvidia,openai,gemini,claude,grok,custom}` | Select the AI provider |
| `--model MODEL` | Override the default model ID |
| `--api-key API_KEY` | Custom API key (auto-detects provider by prefix if `--provider` is omitted) |
| `--base-url BASE_URL` | Custom OpenAI-compatible base URL |
| `--yes`, `-y` | Auto-approve all tool calls without confirmation prompts |

</details>

---

## 🛠️ Available Kali MCP Tools

| Tool | Endpoint | Purpose |
| :--- | :--- | :--- |
| `execute_command` | `/api/command` | Arbitrary Kali shell commands (`searchsploit`, `openssl`, `dig`, `curl`, etc.) |
| `nmap_scan` | `/api/tools/nmap` | Network port & service discovery |
| `gobuster_scan` | `/api/tools/gobuster` | Directory, DNS, fuzz, and vhost enumeration |
| `dirb_scan` | `/api/tools/dirb` | Web content directory scanning |
| `nikto_scan` | `/api/tools/nikto` | Web server vulnerability scanning |
| `sqlmap_scan` | `/api/tools/sqlmap` | Automated SQL injection testing |
| `wpscan_analyze` | `/api/tools/wpscan` | WordPress vulnerability enumeration |
| `enum4linux_scan` | `/api/tools/enum4linux` | Windows/Samba SMB enumeration |
| `hydra_attack` | `/api/tools/hydra` | Network login brute-forcing |
| `john_crack` | `/api/tools/john` | Password hash cracking (John the Ripper) |
| `metasploit_run` | `/api/tools/metasploit` | Metasploit module execution |

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

## 🔧 Troubleshooting

- **`kali-server-mcp` Offline:** Run `./kali-mcp-manager.sh restart` and inspect `/tmp/kali-server-mcp.log`.
- **Missing API Key Error:** Ensure a `.env` file exists in the project root (see `.env.example`), export the matching provider variable (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, or `NVIDIA_API_KEY`), or configure it via **`🔑 API Keys`** in the Desktop GUI.
- **Localhost Proxy Interference:** Automatically bypassed in `kali_core.py` (`http_session.trust_env = False`) and via `NO_PROXY=localhost,127.0.0.1` in the launcher scripts.
- **IDE Import Warnings (`openai` / `PySide6`):** Point your editor's Python interpreter to `/usr/bin/python3` where the system packages are installed.

---

## 🗺️ Roadmap

- [x] Custom wordlist picker and advanced flags panel in the GUI
- [x] Single HTML/Markdown session report export (Raw Output + AI Analysis + Findings)
- [x] Streaming token output for real-time AI responses
- [x] Persistent SQLite lab/CTF workspaces and structured Findings table
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
