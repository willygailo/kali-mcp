# Kali Linux MCP Setup & AI Terminal Assistant

Setup para sa **mcp-kali-server** at AI Terminal Assistant sa iyong Kali Linux gamit ang **NVIDIA NIM** (Nemotron) at **OpenAI**.

---

## 📌 Mga File sa Direktoryong Ito

- **`run-gui.sh` / `kali-gui.py`**: Dedicated **Desktop GUI** (PySide6) na may side-by-side layout: Target, quick presets, at AI prompt sa kaliwa; live raw output at AI analysis sa kanan.
- **`run-agent.sh`**: One-command launcher na nagpapatakbo sa background server at nagbubukas ng AI terminal agent gamit ang **NVIDIA NIM** (Default).
- **`kali-agent.py`**: Terminal AI Agent na may tool calling para sa Kali pentest tools (`nmap`, `gobuster`, `nikto`, `sqlmap`, `john`, raw commands, etc.).
- **`kali_core.py`**: Shared core module para sa Kali MCP API calls, provider configuration, at AI agent loop.
- **`kali-mcp-manager.sh`**: Script para i-start, i-stop, i-restart, at i-check ang status ng Kali API Server (`kali-server-mcp`).

---

## 🖥️ Paano Gamitin ang Desktop GUI

```bash
cd /home/willygailo/Downloads/kali-mcp
./run-gui.sh
```

1. Ilagay ang **Target** (IP, domain, o URL) sa kaliwang bahagi at pumili ng preset (hal. `Nmap (-sCV)`, `Nikto Web`, `TLS / DNS Info`) o mag-type ng AI prompt.
2. Pindutin ang **`▶ Run with AI`** (para may AI summary) o **`⚡ Direct Tool`** (para direktang tool output).
3. Makikita agad ang **Raw Tool Output** at **AI Analysis** sa kanang bahagi.

---

## 🚀 Paano Gamitin sa Terminal

Pumunta sa folder:
```bash
cd /home/willygailo/Downloads/kali-mcp
```

### 1. Simulan ang Interactive AI Chat (NVIDIA Nemotron - Default)
```bash
./run-agent.sh
```

### 2. Magpatakbo ng Direct / One-shot Command
```bash
./run-agent.sh "Scan 127.0.0.1 for open ports with nmap"
```
*(Mag-add ng `--yes` o `-y` kung gusto mong awtomatikong i-execute ang tools nang walang confirmation prompt).*

### 3. Pagpalit ng AI Provider (NVIDIA vs OpenAI)
- **NVIDIA NIM (Active & Working):**
  ```bash
  ./run-agent.sh
  ```
- **OpenAI (Kung may credits na):**
  ```bash
  ./run-agent.sh --provider openai --model gpt-4o
  ```

---

## 🛑 Pag-manage ng Kali API Server

- **Status check**:
  ```bash
  ./kali-mcp-manager.sh status
  ```
- **Stop server**:
  ```bash
  ./kali-mcp-manager.sh stop
  ```
- **Restart server**:
  ```bash
  ./kali-mcp-manager.sh restart
  ```
