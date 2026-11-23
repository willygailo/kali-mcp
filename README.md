# 🐉 Kali MCP AI Workbench

> **AI-powered Offensive Security & Recon Assistant** for **Kali Linux** (`kali-server-mcp`) — featuring a dedicated **PySide6 Desktop GUI** (side-by-side layout) and an **Interactive Terminal Agent** powered by **NVIDIA NIM** (Nemotron) and **OpenAI**.

<p align="left">
  <img src="https://img.shields.io/badge/Kali-Linux-557C94?style=flat-square&logo=kalilinux&logoColor=white" alt="Kali Linux" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PySide6" />
  <img src="https://img.shields.io/badge/LLM-NVIDIA%20NIM%20%7C%20OpenAI-76B900?style=flat-square" alt="LLM Providers" />
  <a href="https://github.com/willygailo/kali-mcp/graphs/contributors?from=2026-08-21T16%3A00%3A00.000Z">
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

- **Side-by-Side Desktop GUI (`kali-gui.py`):**
  - **Left Pane (Controls):** Target input (`IP / Domain / URL`), 6 one-click scan presets (`Nmap (-sCV)`, `Full Recon`, `Nikto Web`, `Gobuster Dir`, `SQLmap`, `TLS / DNS Info`), custom AI prompt, Direct Tool runner, and clickable scan history.
  - **Right Pane (Instant Results):** View **Raw Tool Output / Terminal Log** (top) and **AI Analysis & Findings** (bottom) at the same time — complete with `Analyze Output with AI`, `Copy`, and `Save .txt` / `Save .md`.
  - **Safe Execution:** Toggleable **Auto-approve** mode or an inline **Approve / Decline** banner before running any tool.
- **Interactive Terminal Agent (`kali-agent.py`):** Uses `rich` markdown and panel formatting for headless or SSH workflows.
- **Dual Mode (AI + Direct):** Let the AI orchestrate and summarize (`▶ Run with AI`) or execute Kali tools directly against `kali-server-mcp` (`⚡ Direct Tool`) without an LLM roundtrip.
- **Automatic `.env` Loading:** API keys stay safely out of version control in `.env` (gitignored) and are loaded automatically by the launchers and `kali_core.py`.

---

## 📁 Project Structure

| File | Description |
| :--- | :--- |
| `kali-gui.py` | PySide6 Desktop GUI (`KaliGuiWindow`) with background worker threads and live server status |
| `kali-agent.py` | Interactive and one-shot CLI AI assistant powered by `rich` |
| `kali_core.py` | Shared core: `.env` loader, provider config, `TOOL_DEFINITIONS`, `call_kali_api`, and agent loop |
| `run-gui.sh` | One-command launcher that starts `kali-server-mcp` and opens the Desktop GUI |
| `run-agent.sh` | One-command launcher that starts `kali-server-mcp` and opens the Terminal Agent |
| `kali-mcp-manager.sh` | Control script for `/usr/bin/kali-server-mcp` (`start`, `stop`, `restart`, `status`) |
| `.env.example` | Template for API keys (`NVIDIA_API_KEY`, `OPENAI_API_KEY`) |
| `CONTRIBUTING.md` | Contribution workflow and verification guidelines |

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Kali Linux with **`kali-server-mcp`** installed (`/usr/bin/kali-server-mcp`)
- Python 3 packages: `openai`, `requests`, `PySide6` (for GUI), and `rich` (optional for CLI formatting)

```bash
pip install openai requests PySide6 rich
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and add your API key(s):

```bash
cp .env.example .env
```

```env
NVIDIA_API_KEY="nvapi-your-nvidia-api-key"
NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

# Optional fallback
OPENAI_API_KEY="sk-your-openai-api-key"
```

---

## 🚀 Usage

### 🖥️ Desktop GUI (Recommended)
```bash
./run-gui.sh
```
1. Enter your **Target** (`IP`, `domain`, or `URL`) in the left pane.
2. Pick a **Quick Preset** or type a custom prompt.
3. Click **`▶ Run with AI`** for automated scanning + AI analysis, or **`⚡ Direct Tool`** for immediate raw tool output.
4. Inspect **Raw Tool Output** and **AI Analysis** side-by-side in the right pane, and export results via `Save .txt` or `Save .md`.

### 💻 Terminal CLI Agent
- **Interactive chat (NVIDIA NIM default):**
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
- **Switch to OpenAI provider:**
  ```bash
  ./run-agent.sh --provider openai --model gpt-4o
  ```

<details>
<summary>All CLI Options for <code>kali-agent.py</code></summary>

| Flag | Description |
| :--- | :--- |
| `prompt` | Optional initial prompt for one-shot execution |
| `--provider {nvidia,openai}` | Select the AI provider |
| `--model MODEL` | Override the default model ID |
| `--api-key API_KEY` | Custom API key |
| `--base-url BASE_URL` | Custom OpenAI-compatible base URL |
| `--yes`, `-y` | Auto-approve all tool calls without confirmation prompts |

</details>

---

## 🛠️ Available Kali MCP Tools

| Tool | Endpoint | Purpose |
| :--- | :--- | :--- |
| `execute_command` | `/api/command` | Arbitrary Kali shell commands (`openssl`, `dig`, `curl`, etc.) |
| `nmap_scan` | `/api/tools/nmap` | Network port & service discovery |
| `gobuster_scan` | `/api/tools/gobuster` | Directory, DNS, fuzz, and vhost enumeration |
| `nikto_scan` | `/api/tools/nikto` | Web server vulnerability scanning |
| `sqlmap_scan` | `/api/tools/sqlmap` | Automated SQL injection testing |
| `john_crack` | `/api/tools/john` | Password hash cracking (John the Ripper) |

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
- **Missing API Key Error:** Ensure a `.env` file exists in the project root (see `.env.example`) or export `NVIDIA_API_KEY` / `OPENAI_API_KEY`.
- **Localhost Proxy Interference:** Automatically bypassed in `kali_core.py` (`http_session.trust_env = False`) and via `NO_PROXY=localhost,127.0.0.1` in the launcher scripts.
- **IDE Import Warnings (`openai` / `PySide6`):** Point your editor's Python interpreter to `/usr/bin/python3` where the system packages are installed.

---

## 🗺️ Roadmap

- [ ] Custom wordlist picker and saved scan profiles in the GUI
- [ ] Single HTML/Markdown session report export (Raw Output + AI Analysis)
- [ ] Streaming token output for real-time AI responses

---

## 👥 Contributors

Thanks to everyone who has contributed to this project! View the live contribution graph on [GitHub Contributors](https://github.com/willygailo/kali-mcp/graphs/contributors?from=2026-08-21T16%3A00%3A00.000Z).

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

<a href="https://github.com/willygailo/kali-mcp/graphs/contributors?from=2026-08-21T16%3A00%3A00.000Z">
  <img src="https://contrib.rocks/image?repo=willygailo/kali-mcp" alt="Contributors Graph" />
</a>

> Want to contribute? Check out [CONTRIBUTING.md](CONTRIBUTING.md) and open a Pull Request!

---

## ⚠️ Responsible Use Notice
Use this tool strictly for **authorized penetration testing engagements, personal lab environments, or CTF challenges**.
