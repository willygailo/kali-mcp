# Contributing to Kali MCP AI Workbench

Salamat sa interes mong mag-ambag sa **kali-mcp**! Bukas ang proyektong ito sa mga bug fixes, bagong Kali tool integrations, UI improvements, at documentation updates.

---

## 🛠️ Paano Mag-setup para sa Development

1. **I-fork at i-clone ang repo:**
   ```bash
   git clone https://github.com/willygailo/kali-mcp.git
   cd kali-mcp
   ```

2. **I-install ang dependencies:**
   ```bash
   pip install openai requests PySide6 rich ruff
   ```

3. **I-setup ang local `.env`:**
   ```bash
   cp .env.example .env
   ```
   > ⚠️ **Huwag kailanman mag-commit ng `.env` o hardcoded API keys.**

---

## ✅ Bago Mag-submit ng Pull Request

Siguraduhing pumapasa ang mga sumusunod na checks:

```bash
# Lint at syntax check
ruff check app/kali_core.py app/kali-agent.py app/kali-gui.py
python3 -m py_compile app/kali_core.py app/kali-agent.py app/kali-gui.py

# CLI check
python3 app/kali-agent.py --help

# Headless GUI smoke test
QT_QPA_PLATFORM=offscreen python3 -c "
import sys, importlib.util
from PySide6.QtWidgets import QApplication
spec = importlib.util.spec_from_file_location('kali_gui', 'app/kali-gui.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
app = QApplication(sys.argv)
win = mod.KaliGuiWindow()
win.close()
print('OK')
"
```

---

## 📬 Workflow ng Pull Request

1. Gumawa ng feature branch (`git checkout -b feat/pangalan-ng-feature`).
2. I-keep na malinis ang diff at iwasan ang unrelated changes.
3. Magbukas ng Pull Request sa `main` na may maikling paliwanag kung ano ang binago at paano ito na-verify.
