#!/usr/bin/env python3
"""
Kali MCP Desktop GUI (Advanced Workbench)
-----------------------------------------
Side-by-side PySide6 GUI for Kali Linux MCP:
- Top bar: Persistent SQLite Engagement/Project switcher, live server/tool status, LLM provider/model.
- Left pane: Target input, presets, automated recon playbooks, advanced tool flags/wordlist picker,
  AI prompt, direct tool runner, elapsed scan timer, and persisted scan history.
- Right pane: Tabbed live view with simultaneous Raw Output + Streaming AI Analysis,
  auto-parsed Findings & Ports table with follow-up triggers, and Lab/CTF Notes + Report Export.
"""

import html
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from PySide6.QtCore import QRect, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kali_core import (
    AgentCallbacks,
    DEFAULT_KALI_SERVER_URL,
    PLAYBOOKS,
    PROVIDER_REGISTRY,
    SYSTEM_PROMPT,
    call_kali_api,
    create_openai_client,
    get_kali_server_health,
    resolve_provider_config,
    run_chat_turn,
    save_env_keys,
    test_provider_connection,
)
from kali_parsers import parse_tool_output
from kali_reports import generate_html_report, generate_markdown_report
from kali_store import ProjectStore

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGER_SCRIPT = os.path.join(SCRIPT_DIR, "kali-mcp-manager.sh")

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}
QLabel, QCheckBox {
    background-color: transparent;
}
QFrame#PanelCard {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
}
QFrame#TopBar {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
}
QFrame#ApprovalBar {
    background-color: #2b1d12;
    border: 1px solid #d29922;
    border-radius: 8px;
}
QLabel#SectionTitle {
    color: #58a6ff;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLineEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: #1f6feb;
}
QHeaderView::section {
    background-color: #161b22;
    color: #58a6ff;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 6px;
    font-weight: 700;
    font-size: 11px;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #58a6ff;
}
QLineEdit#TargetInput {
    font-size: 14px;
    font-weight: 600;
    padding: 8px 10px;
    border: 1px solid #388bfd;
}
QTextEdit#RawOutput, QTextBrowser#AiOutput {
    background-color: #090c10;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px;
}
QTextEdit#RawOutput {
    font-family: "JetBrains Mono", "Fira Code", "DejaVu Sans Mono", monospace;
    font-size: 12px;
}
QTabWidget::pane {
    border: none;
}
QTabBar::tab {
    background-color: #161b22;
    color: #8b949e;
    border: 1px solid #30363d;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 7px 14px;
    margin-right: 4px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #0d1117;
    color: #58a6ff;
    border-color: #388bfd;
}
QProgressBar {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    text-align: center;
    height: 16px;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #238636;
}
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 11px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:disabled {
    color: #6e7681;
    background-color: #161b22;
    border-color: #21262d;
}
QPushButton#PrimaryBtn {
    background-color: #238636;
    border-color: #2ea043;
    color: #ffffff;
}
QPushButton#PrimaryBtn:hover {
    background-color: #2ea043;
}
QPushButton#DirectBtn {
    background-color: #1f6feb;
    border-color: #388bfd;
    color: #ffffff;
}
QPushButton#DirectBtn:hover {
    background-color: #388bfd;
}
QPushButton#DangerBtn {
    background-color: #da3633;
    border-color: #f85149;
    color: #ffffff;
}
QPushButton#DangerBtn:hover {
    background-color: #f85149;
}
QPushButton#PresetBtn {
    background-color: #161b22;
    border: 1px solid #30363d;
    padding: 5px 6px;
    font-size: 11px;
}
QPushButton#PresetBtn:hover {
    border-color: #58a6ff;
    color: #58a6ff;
}
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QScrollBar:vertical {
    background-color: #0d1117;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background-color: #8b949e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QSplitter::handle {
    background-color: #30363d;
}
QSplitter::handle:horizontal {
    width: 4px;
}
QSplitter::handle:vertical {
    height: 4px;
}
"""


class AgentWorker(QThread):
    """Runs a streaming AI agent chat turn in a background thread."""

    reasoning_received = Signal(str)
    assistant_delta = Signal(str)
    assistant_received = Signal(str)
    tool_planned = Signal(str, dict, str)
    approval_requested = Signal(str, dict, str)
    tool_executing = Signal(str, dict)
    tool_result_received = Signal(str, dict)
    error_received = Signal(str, str)
    finished_turn = Signal(list)

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: Optional[str],
        base_url: Optional[str],
        messages: List[Dict[str, Any]],
        auto_approve: bool,
    ):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.messages = [dict(m) for m in messages]
        self.auto_approve = auto_approve
        self._stop_requested = False
        self._approval_event = threading.Event()
        self._approval_result = False
        self._active_session: Optional[requests.Session] = None

    def request_stop(self):
        self._stop_requested = True
        self._approval_result = False
        self._approval_event.set()
        if self._active_session is not None:
            try:
                self._active_session.close()
            except Exception:
                pass

    def provide_approval(self, approved: bool):
        self._approval_result = approved
        self._approval_event.set()

    def run(self):
        client = create_openai_client(self.api_key, self.base_url)

        def on_confirm(fn_name: str, fn_args: Dict[str, Any], cmd_preview: str) -> bool:
            if self._stop_requested:
                return False
            self._approval_event.clear()
            self.approval_requested.emit(fn_name, fn_args, cmd_preview)
            self._approval_event.wait()
            return self._approval_result

        def set_session(sess: Optional[requests.Session]):
            self._active_session = sess

        callbacks = AgentCallbacks(
            on_reasoning=lambda text: self.reasoning_received.emit(text),
            on_assistant_delta=lambda chunk: self.assistant_delta.emit(chunk),
            on_assistant_message=lambda text: self.assistant_received.emit(text),
            on_tool_planned=lambda name, args, prev: self.tool_planned.emit(name, args, prev),
            on_confirm=on_confirm,
            on_tool_executing=lambda name, args: self.tool_executing.emit(name, args),
            on_tool_result=lambda name, res: self.tool_result_received.emit(name, res),
            on_error=lambda etype, msg: self.error_received.emit(etype, msg),
            should_stop=lambda: self._stop_requested,
            on_http_session=set_session,
        )

        run_chat_turn(
            client=client,
            model=self.model,
            messages=self.messages,
            auto_approve=self.auto_approve,
            callbacks=callbacks,
            stream=True,
        )
        self.finished_turn.emit(self.messages)


class DirectToolWorker(QThread):
    """Runs a direct tool call against kali-server-mcp without an LLM roundtrip."""

    tool_result_received = Signal(str, dict)
    finished_direct = Signal()

    def __init__(self, tool_name: str, tool_args: Dict[str, Any]):
        super().__init__()
        self.tool_name = tool_name
        self.tool_args = tool_args
        self._active_session: Optional[requests.Session] = None

    def request_stop(self):
        if self._active_session is not None:
            try:
                self._active_session.close()
            except Exception:
                pass

    def run(self):
        def set_session(sess: Optional[requests.Session]):
            self._active_session = sess

        result = call_kali_api(self.tool_name, self.tool_args, on_session=set_session)
        self.tool_result_received.emit(self.tool_name, result)
        self.finished_direct.emit()


class PlaybookWorker(QThread):
    """Executes a multi-step recon playbook sequentially."""

    step_progress = Signal(int, int, str)
    tool_result_received = Signal(str, dict)
    finished_playbook = Signal(bool, str)

    def __init__(self, target: str, steps: List[Dict[str, Any]], wordlist: str, extra_args: str):
        super().__init__()
        self.target = target
        self.steps = steps
        self.wordlist = wordlist
        self.extra_args = extra_args
        self._stop_requested = False
        self._active_session: Optional[requests.Session] = None

    def request_stop(self):
        self._stop_requested = True
        if self._active_session is not None:
            try:
                self._active_session.close()
            except Exception:
                pass

    def run(self):
        total = len(self.steps)
        summaries: List[str] = []

        def set_session(sess: Optional[requests.Session]):
            self._active_session = sess

        for idx, step in enumerate(self.steps, start=1):
            if self._stop_requested:
                self.finished_playbook.emit(False, "Playbook stopped by user.")
                return

            label = step["label"]
            tool = step["tool"]
            base_args = dict(step.get("args", {}))
            self.step_progress.emit(idx, total, label)

            if tool == "tls_http_check":
                host = self.target.replace("https://", "").replace("http://", "").split("/")[0]
                qhost = shlex.quote(host)
                url = self.target if self.target.startswith(("http://", "https://")) else f"https://{host}"
                qurl = shlex.quote(url)
                cmd = (
                    f"curl -skI --max-time 10 {qurl} | head -n 25; "
                    f"echo '--- TLS ---'; "
                    f"echo | openssl s_client -connect {qhost}:443 -servername {qhost} 2>&1 | head -n 45"
                )
                api_tool = "execute_command"
                args: Dict[str, Any] = {"command": cmd}
            elif tool == "gobuster_scan":
                url = self.target if self.target.startswith(("http://", "https://")) else f"http://{self.target}"
                api_tool = "gobuster_scan"
                args = {
                    "url": url,
                    "mode": base_args.get("mode", "dir"),
                    "wordlist": self.wordlist or "/usr/share/wordlists/dirb/common.txt",
                    "additional_args": self.extra_args,
                }
            elif tool == "nikto_scan":
                api_tool = "nikto_scan"
                args = {"target": self.target, "additional_args": self.extra_args}
            elif tool == "nmap_scan":
                api_tool = "nmap_scan"
                args = {
                    "target": self.target,
                    "scan_type": base_args.get("scan_type", "-sCV"),
                    "ports": base_args.get("ports", ""),
                    "additional_args": base_args.get("additional_args", "-T4"),
                }
            else:
                api_tool = tool
                args = {"target": self.target, **base_args}

            res = call_kali_api(api_tool, args, on_session=set_session)
            self.tool_result_received.emit(tool if tool == "tls_http_check" else api_tool, res)
            out_snip = (res.get("stdout") or res.get("error") or "").strip()[:3000]
            summaries.append(f"[{label}]\n{out_snip}")

        self.finished_playbook.emit(True, "\n\n".join(summaries))


class ServerActionWorker(QThread):
    """Runs kali-mcp-manager.sh start|stop|restart asynchronously."""

    completed = Signal(bool, str)

    def __init__(self, action: str):
        super().__init__()
        self.action = action

    def run(self):
        try:
            proc = subprocess.run(
                [MANAGER_SCRIPT, self.action],
                capture_output=True,
                text=True,
                timeout=15,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            self.completed.emit(proc.returncode == 0, out.strip())
        except Exception as exc:
            self.completed.emit(False, str(exc))


class TestKeyWorker(QThread):
    """Runs a lightweight provider connectivity check in a background thread."""

    completed = Signal(str, bool, str)

    def __init__(
        self,
        provider: str,
        api_key: Optional[str],
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__()
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def run(self):
        try:
            res = test_provider_connection(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model,
                base_url=self.base_url,
            )
            ok = bool(res.get("ok"))
            msg = str(res.get("message") or ("Connection successful." if ok else "Connection failed."))
            self.completed.emit(self.provider, ok, msg)
        except Exception as exc:
            self.completed.emit(self.provider, False, str(exc))


class ApiKeysDialog(QDialog):
    """Modal dialog for viewing, testing, and saving LLM provider API keys to .env."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("LLM API Keys Manager")
        self.setMinimumWidth(560)
        if parent is None:
            self.setStyleSheet(DARK_STYLESHEET)

        self.saved_path: Optional[str] = None
        self.key_inputs: Dict[str, QLineEdit] = {}
        self.status_badges: Dict[str, QLabel] = {}
        self.show_buttons: Dict[str, QPushButton] = {}
        self.test_buttons: Dict[str, QPushButton] = {}
        self._active_workers: set[TestKeyWorker] = set()

        self._build_ui()
        self._fit_dialog_to_screen()

    def _fit_dialog_to_screen(self):
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen is not None else QRect(0, 0, 1280, 720)
        w = min(680, int(avail.width() * 0.9))
        h = min(600, int(avail.height() * 0.88))
        self.resize(w, h)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel("Configure LLM Provider API Keys")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #58a6ff;")
        layout.addWidget(header)

        sub = QLabel(
            "Keys are saved locally to .env (chmod 600) and applied immediately to the active session."
        )
        sub.setStyleSheet("color: #8b949e; font-size: 12px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_body = QWidget()
        scroll_layout = QVBoxLayout(scroll_body)
        scroll_layout.setContentsMargins(0, 0, 4, 0)
        scroll_layout.setSpacing(10)

        # Standard cloud providers card
        providers_card = QFrame()
        providers_card.setObjectName("PanelCard")
        grid = QGridLayout(providers_card)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(8)
        grid.setColumnStretch(2, 1)

        standard_keys = [k for k in PROVIDER_REGISTRY if k != "custom"]
        for row, pkey in enumerate(standard_keys):
            meta = PROVIDER_REGISTRY[pkey]
            cfg = resolve_provider_config(provider=pkey)
            initial_key = str(cfg.get("api_key") or "")

            name_lbl = QLabel(str(meta.get("label", pkey)))
            name_lbl.setStyleSheet("font-weight: 700;")
            name_lbl.setToolTip(str(meta.get("env_key", "")))

            key_edit, show_btn, test_btn, badge_lbl = self._create_key_controls(
                pkey,
                initial_key,
                f"Enter {meta.get('env_key', 'API_KEY')}...",
            )

            grid.addWidget(name_lbl, row, 0)
            grid.addWidget(badge_lbl, row, 1)
            grid.addWidget(key_edit, row, 2)
            grid.addWidget(show_btn, row, 3)
            grid.addWidget(test_btn, row, 4)
            self._update_badge(pkey)

        scroll_layout.addWidget(providers_card)

        # Custom / Local OpenAI-compatible endpoint card
        custom_meta = PROVIDER_REGISTRY.get("custom", {})
        custom_card = QFrame()
        custom_card.setObjectName("PanelCard")
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(12, 12, 12, 12)
        custom_layout.setSpacing(8)

        custom_hdr = QHBoxLayout()
        custom_title = QLabel(str(custom_meta.get("label", "Custom / Local")))
        custom_title.setObjectName("SectionTitle")
        custom_hdr.addWidget(custom_title)
        custom_hdr.addStretch()

        custom_key_edit, custom_show_btn, custom_test_btn, custom_badge = self._create_key_controls(
            "custom",
            os.environ.get(str(custom_meta.get("env_key", "CUSTOM_API_KEY")), ""),
            "Optional API key (leave blank for local Ollama / LM Studio)",
        )
        custom_hdr.addWidget(custom_badge)
        custom_hdr.addWidget(custom_test_btn)
        custom_layout.addLayout(custom_hdr)

        custom_grid = QGridLayout()
        custom_grid.setSpacing(8)
        custom_grid.setColumnStretch(1, 1)

        base_url_env = str(custom_meta.get("base_url_env", "CUSTOM_BASE_URL"))
        model_env = str(custom_meta.get("model_env", "CUSTOM_MODEL"))
        default_custom_model = str(custom_meta.get("default_model", "llama3.2"))

        self.custom_base_url_input = QLineEdit(os.environ.get(base_url_env, ""))
        self.custom_base_url_input.setPlaceholderText("e.g. http://localhost:11434/v1")
        self.custom_base_url_input.textChanged.connect(lambda _txt: self._update_badge("custom"))

        self.custom_api_key_input = custom_key_edit

        self.custom_model_input = QLineEdit(os.environ.get(model_env, ""))
        self.custom_model_input.setPlaceholderText(f"e.g. {default_custom_model}")

        custom_key_row = QHBoxLayout()
        custom_key_row.setSpacing(6)
        custom_key_row.addWidget(self.custom_api_key_input, 1)
        custom_key_row.addWidget(custom_show_btn)

        custom_grid.addWidget(QLabel("Base URL:"), 0, 0)
        custom_grid.addWidget(self.custom_base_url_input, 0, 1)
        custom_grid.addWidget(QLabel("API Key:"), 1, 0)
        custom_grid.addLayout(custom_key_row, 1, 1)
        custom_grid.addWidget(QLabel("Model:"), 2, 0)
        custom_grid.addWidget(self.custom_model_input, 2, 1)

        custom_layout.addLayout(custom_grid)
        self._update_badge("custom")
        scroll_layout.addWidget(custom_card)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_body)
        layout.addWidget(scroll, 1)

        self.test_status_lbl = QLabel("")
        self.test_status_lbl.setWordWrap(True)
        self.test_status_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        layout.addWidget(self.test_status_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.reject)

        self.btn_save = QPushButton("💾 Save to .env")
        self.btn_save.setObjectName("PrimaryBtn")
        self.btn_save.clicked.connect(self._save_keys)

        btn_row.addWidget(self.btn_close)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

    def _create_key_controls(
        self,
        provider_key: str,
        initial_key: str,
        placeholder: str,
    ) -> tuple[QLineEdit, QPushButton, QPushButton, QLabel]:
        key_edit = QLineEdit(initial_key)
        key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_edit.setPlaceholderText(placeholder)
        key_edit.textChanged.connect(lambda _txt, k=provider_key: self._update_badge(k))

        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.setFixedWidth(58)
        show_btn.toggled.connect(lambda checked, k=provider_key: self._toggle_key_visibility(k, checked))

        test_btn = QPushButton("Test")
        test_btn.setFixedWidth(74)
        test_btn.clicked.connect(lambda _=False, k=provider_key: self._run_test(k))

        badge_lbl = QLabel()
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_lbl.setFixedWidth(88)

        self.key_inputs[provider_key] = key_edit
        self.show_buttons[provider_key] = show_btn
        self.test_buttons[provider_key] = test_btn
        self.status_badges[provider_key] = badge_lbl
        return key_edit, show_btn, test_btn, badge_lbl

    def _toggle_key_visibility(self, provider_key: str, checked: bool):
        edit = self.key_inputs[provider_key]
        btn = self.show_buttons[provider_key]
        edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        btn.setText("Hide" if checked else "Show")

    def _update_badge(self, provider_key: str):
        badge = self.status_badges[provider_key]
        if provider_key == "custom":
            configured = bool(
                self.custom_base_url_input.text().strip() or self.custom_api_key_input.text().strip()
            )
        else:
            configured = bool(self.key_inputs[provider_key].text().strip())

        badge.setText("Configured" if configured else "Missing")
        if configured:
            badge.setStyleSheet(
                "background-color: #122d1b; color: #3fb950; border: 1px solid #2ea043; "
                "border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 700;"
            )
        else:
            badge.setStyleSheet(
                "background-color: #2d1b16; color: #f85149; border: 1px solid #da3633; "
                "border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 700;"
            )

    def _set_test_feedback(self, provider_key: str, ok: Optional[bool], message: str):
        label = PROVIDER_REGISTRY.get(provider_key, {}).get("label", provider_key)
        if ok is None:
            self.test_status_lbl.setStyleSheet("color: #d29922; font-weight: 600;")
            self.test_status_lbl.setText(f"⏳ {label}: {message}")
        elif ok:
            self.test_status_lbl.setStyleSheet("color: #3fb950; font-weight: 600;")
            self.test_status_lbl.setText(f"✓ {label}: {message}")
        else:
            self.test_status_lbl.setStyleSheet("color: #f85149; font-weight: 600;")
            self.test_status_lbl.setText(f"✗ {label}: {message}")

    def _run_test(self, provider_key: str):
        meta = PROVIDER_REGISTRY.get(provider_key, {})
        api_key = self.key_inputs[provider_key].text().strip() or None
        if provider_key == "custom":
            base_url = self.custom_base_url_input.text().strip() or None
            model = self.custom_model_input.text().strip() or meta.get("default_model")
            if not base_url:
                self._set_test_feedback(provider_key, False, "Enter a Base URL before testing Custom / Local.")
                return
        else:
            base_url = meta.get("default_base_url")
            model = meta.get("default_model")
            if not api_key:
                self._set_test_feedback(provider_key, False, f"Enter {meta.get('env_key', 'an API key')} first.")
                return

        btn = self.test_buttons[provider_key]
        btn.setEnabled(False)
        btn.setText("...")
        self._set_test_feedback(provider_key, None, "Testing connection...")

        worker = TestKeyWorker(provider=provider_key, api_key=api_key, model=model, base_url=base_url)
        self._active_workers.add(worker)
        worker.completed.connect(self._on_test_completed)
        worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
        worker.start()

    def _on_worker_finished(self, worker: TestKeyWorker):
        self._active_workers.discard(worker)
        worker.deleteLater()

    def _on_test_completed(self, provider_key: str, ok: bool, message: str):
        btn = self.test_buttons.get(provider_key)
        if btn is not None:
            btn.setEnabled(True)
            btn.setText("Test")
        self._set_test_feedback(provider_key, ok, message)

    def _save_keys(self):
        updates: Dict[str, str] = {}
        for pkey, meta in PROVIDER_REGISTRY.items():
            env_key = meta.get("env_key")
            if env_key and pkey in self.key_inputs:
                updates[str(env_key)] = self.key_inputs[pkey].text().strip()

        custom_meta = PROVIDER_REGISTRY.get("custom", {})
        base_url_env = custom_meta.get("base_url_env")
        model_env = custom_meta.get("model_env")
        if base_url_env:
            updates[str(base_url_env)] = self.custom_base_url_input.text().strip()
        if model_env:
            updates[str(model_env)] = self.custom_model_input.text().strip()

        self.saved_path = save_env_keys(updates)
        self.accept()


class KaliGuiWindow(QMainWindow):
    def __init__(self, store: Optional[ProjectStore] = None):
        super().__init__()
        self.setWindowTitle("Kali MCP AI Workbench")

        self.store = store or ProjectStore()
        self.current_engagement_id: int = 1
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.history_entries: List[Dict[str, Any]] = []
        self.current_findings: List[Dict[str, Any]] = []
        self.raw_log_plain = ""
        self.ai_markdown_sections: List[str] = []
        self._streaming_section_index: Optional[int] = None
        self._streaming_buffer = ""
        self.current_worker: Optional[QThread] = None
        self.server_worker: Optional[ServerActionWorker] = None
        self._run_started_at: Optional[float] = None

        self._build_ui()
        self.setStyleSheet(DARK_STYLESHEET)
        self._fit_to_screen()
        self._load_provider_defaults()
        self._load_engagements_combo()
        self.refresh_server_status()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_server_status)
        self.status_timer.start(10000)

        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self._update_elapsed_label)

    def _fit_to_screen(self):
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen is not None else QRect(0, 0, 1280, 720)
        w = min(1320, max(820, int(avail.width() * 0.94)))
        h = min(800, max(600, int(avail.height() * 0.92)))
        x = avail.x() + (avail.width() - w) // 2
        y = avail.y() + (avail.height() - h) // 2
        self.setGeometry(x, y, w, h)
        self.main_splitter.setSizes([int(w * 0.36), int(w * 0.64)])

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        # --- Top Bar (Two-Row Compact Layout) ---
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        self.top_bar = top_bar
        top_vbox = QVBoxLayout(top_bar)
        top_vbox.setContentsMargins(10, 6, 10, 6)
        top_vbox.setSpacing(6)

        # Row 1: Brand | Project | stretch | Server status & controls
        top_row1 = QHBoxLayout()
        top_row1.setSpacing(6)

        title_lbl = QLabel("KALI MCP AI WORKBENCH")
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #58a6ff; letter-spacing: 0.6px;")
        top_row1.addWidget(title_lbl)

        top_row1.addWidget(QLabel("Project:"))
        self.engagement_combo = QComboBox()
        self.engagement_combo.setMinimumWidth(140)
        self.engagement_combo.currentIndexChanged.connect(self._on_engagement_changed)
        top_row1.addWidget(self.engagement_combo)

        btn_new_proj = QPushButton("+ New")
        btn_new_proj.clicked.connect(self.create_new_engagement)
        btn_del_proj = QPushButton("Del")
        btn_del_proj.clicked.connect(self.delete_current_engagement)
        top_row1.addWidget(btn_new_proj)
        top_row1.addWidget(btn_del_proj)

        top_row1.addStretch()

        self.server_status_lbl = QLabel("● Checking...")
        self.server_status_lbl.setStyleSheet("color: #d29922; font-weight: 600;")
        top_row1.addWidget(self.server_status_lbl)

        self.btn_start_srv = QPushButton("Start")
        self.btn_start_srv.clicked.connect(lambda: self.run_server_action("start"))
        self.btn_restart_srv = QPushButton("Restart")
        self.btn_restart_srv.clicked.connect(lambda: self.run_server_action("restart"))
        self.btn_stop_srv = QPushButton("Stop")
        self.btn_stop_srv.clicked.connect(lambda: self.run_server_action("stop"))
        top_row1.addWidget(self.btn_start_srv)
        top_row1.addWidget(self.btn_restart_srv)
        top_row1.addWidget(self.btn_stop_srv)

        # Row 2: LLM Provider, Model, API Keys | stretch
        top_row2 = QHBoxLayout()
        top_row2.setSpacing(6)

        top_row2.addWidget(QLabel("LLM:"))
        self.provider_combo = QComboBox()
        for key, meta in PROVIDER_REGISTRY.items():
            self.provider_combo.addItem(str(meta.get("label", key)), key)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        top_row2.addWidget(self.provider_combo)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.model_combo.setMinimumWidth(180)
        self.model_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_row2.addWidget(self.model_combo, 1)

        self.btn_api_keys = QPushButton("🔑 API Keys")
        self.btn_api_keys.setToolTip("Configure and test API keys for OpenAI, Gemini, Claude, Grok, NVIDIA, or Custom")
        self.btn_api_keys.clicked.connect(self.open_api_keys_dialog)
        top_row2.addWidget(self.btn_api_keys)
        top_row2.addStretch(1)

        top_vbox.addLayout(top_row1)
        top_vbox.addLayout(top_row2)

        root_layout.addWidget(top_bar)

        # --- Main Side-by-Side Splitter ---
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        root_layout.addWidget(self.main_splitter, 1)

        # ================= LEFT PANE: Target & Controls =================
        left_widget = QWidget()
        left_widget.setMinimumWidth(300)
        self.left_widget = left_widget
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        target_card = QFrame()
        target_card.setObjectName("PanelCard")
        tc_layout = QVBoxLayout(target_card)
        tc_layout.setSpacing(7)

        lbl_target = QLabel("Target (IP / Domain / URL)")
        lbl_target.setObjectName("SectionTitle")
        tc_layout.addWidget(lbl_target)

        self.target_input = QLineEdit()
        self.target_input.setObjectName("TargetInput")
        self.target_input.setPlaceholderText("e.g. 10.10.10.5, example.com, https://target.local")
        self.target_input.returnPressed.connect(self.run_ai_scan)
        self.target_input.editingFinished.connect(self._persist_current_target)
        tc_layout.addWidget(self.target_input)

        lbl_presets = QLabel("Quick Presets & Playbooks")
        lbl_presets.setObjectName("SectionTitle")
        tc_layout.addWidget(lbl_presets)

        preset_grid = QGridLayout()
        preset_grid.setSpacing(5)
        presets = [
            ("Nmap (-sCV)", "nmap_scan", "Run an Nmap -sCV -T4 port and service scan on {target} and summarize open ports and risks."),
            ("Full Recon", "nmap_scan", "Perform reconnaissance on {target}: scan ports with nmap, check HTTP headers, TLS cert, and DNS info."),
            ("Nikto Web", "nikto_scan", "Run a Nikto web vulnerability scan against {target} and summarize findings."),
            ("Gobuster Dir", "gobuster_scan", "Run Gobuster directory enumeration on {target} and report discovered paths."),
            ("SQLmap", "sqlmap_scan", "Check {target} with SQLmap and report any SQL injection points."),
            ("TLS / DNS", "tls_dns", "Run openssl s_client certificate/TLS check and dig DNS records on {target}, then summarize findings."),
        ]
        for idx, (label, tool_key, template) in enumerate(presets):
            btn = QPushButton(label)
            btn.setObjectName("PresetBtn")
            btn.clicked.connect(lambda _=False, k=tool_key, t=template: self.apply_preset(k, t))
            preset_grid.addWidget(btn, idx // 3, idx % 3)
        tc_layout.addLayout(preset_grid)

        playbook_row = QHBoxLayout()
        self.btn_pb_web = QPushButton("▶ Web Recon Pipeline")
        self.btn_pb_web.setObjectName("PresetBtn")
        self.btn_pb_web.clicked.connect(lambda: self.run_playbook("web_recon"))
        self.btn_pb_net = QPushButton("▶ Network Audit Pipeline")
        self.btn_pb_net.setObjectName("PresetBtn")
        self.btn_pb_net.clicked.connect(lambda: self.run_playbook("network_audit"))
        playbook_row.addWidget(self.btn_pb_web)
        playbook_row.addWidget(self.btn_pb_net)
        tc_layout.addLayout(playbook_row)

        self.playbook_progress = QProgressBar()
        self.playbook_progress.hide()
        tc_layout.addWidget(self.playbook_progress)

        # Collapsible Advanced Tool Options
        self.adv_toggle = QCheckBox("Advanced Tool Options (Ports, Flags, Wordlist)")
        self.adv_toggle.toggled.connect(self._toggle_advanced_box)
        tc_layout.addWidget(self.adv_toggle)

        self.adv_box = QFrame()
        self.adv_box.setStyleSheet("QFrame { background-color: #0d1117; border: 1px solid #30363d; border-radius: 6px; }")
        adv_layout = QGridLayout(self.adv_box)
        adv_layout.setContentsMargins(8, 8, 8, 8)
        adv_layout.setSpacing(6)

        adv_layout.addWidget(QLabel("Ports:"), 0, 0)
        self.ports_input = QLineEdit()
        self.ports_input.setPlaceholderText("e.g. 80,443 or 1-1000")
        adv_layout.addWidget(self.ports_input, 0, 1)

        adv_layout.addWidget(QLabel("Extra Flags:"), 1, 0)
        self.flags_input = QLineEdit()
        self.flags_input.setPlaceholderText("e.g. -T4 -Pn or --enumerate vp,u")
        adv_layout.addWidget(self.flags_input, 1, 1)

        adv_layout.addWidget(QLabel("Wordlist:"), 2, 0)
        wl_row = QHBoxLayout()
        self.wordlist_input = QLineEdit("/usr/share/wordlists/dirb/common.txt")
        btn_wl_browse = QPushButton("...")
        btn_wl_browse.setMaximumWidth(34)
        btn_wl_browse.clicked.connect(self._browse_wordlist)
        wl_row.addWidget(self.wordlist_input, 1)
        wl_row.addWidget(btn_wl_browse)
        adv_layout.addLayout(wl_row, 2, 1)

        self.adv_box.hide()
        tc_layout.addWidget(self.adv_box)

        lbl_prompt = QLabel("AI Prompt / Custom Command")
        lbl_prompt.setObjectName("SectionTitle")
        tc_layout.addWidget(lbl_prompt)

        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlaceholderText(
            "Enter AI instruction (or shell command when Direct Tool = Custom Shell). Leave blank for quick recon on Target."
        )
        self.prompt_input.setMinimumHeight(64)
        self.prompt_input.setMaximumHeight(110)
        tc_layout.addWidget(self.prompt_input)

        direct_row = QHBoxLayout()
        direct_row.addWidget(QLabel("Direct Tool:"))
        self.direct_tool_combo = QComboBox()
        direct_tools = [
            ("nmap_scan (-sCV -T4)", "nmap_scan"),
            ("nikto_scan", "nikto_scan"),
            ("gobuster_scan (dir)", "gobuster_scan"),
            ("dirb_scan", "dirb_scan"),
            ("sqlmap_scan (--batch)", "sqlmap_scan"),
            ("wpscan_analyze", "wpscan_analyze"),
            ("enum4linux_scan (-a)", "enum4linux_scan"),
            ("tls_dns (openssl + dig)", "tls_dns"),
            ("searchsploit (--json)", "searchsploit"),
            ("Custom Shell (Prompt Box)", "execute_command"),
        ]
        for label, key in direct_tools:
            self.direct_tool_combo.addItem(label, key)
        direct_row.addWidget(self.direct_tool_combo, 1)
        tc_layout.addLayout(direct_row)

        opt_row = QHBoxLayout()
        self.auto_approve_chk = QCheckBox("Auto-approve tool calls")
        self.auto_approve_chk.setChecked(False)
        self.elapsed_lbl = QLabel("")
        self.elapsed_lbl.setStyleSheet("color: #d29922; font-weight: 700;")
        opt_row.addWidget(self.auto_approve_chk)
        opt_row.addStretch()
        opt_row.addWidget(self.elapsed_lbl)
        tc_layout.addLayout(opt_row)

        action_row = QHBoxLayout()
        self.btn_run_ai = QPushButton("▶ Run with AI")
        self.btn_run_ai.setObjectName("PrimaryBtn")
        self.btn_run_ai.clicked.connect(self.run_ai_scan)

        self.btn_run_direct = QPushButton("⚡ Direct Tool")
        self.btn_run_direct.setObjectName("DirectBtn")
        self.btn_run_direct.clicked.connect(self.run_direct_tool)

        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setObjectName("DangerBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_current_run)

        action_row.addWidget(self.btn_run_ai, 2)
        action_row.addWidget(self.btn_run_direct, 2)
        action_row.addWidget(self.btn_stop, 1)
        tc_layout.addLayout(action_row)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setWidget(target_card)
        left_layout.addWidget(left_scroll, 3)

        # History Card (SQLite persisted per engagement)
        hist_card = QFrame()
        hist_card.setObjectName("PanelCard")
        hc_layout = QVBoxLayout(hist_card)
        hc_layout.setContentsMargins(8, 8, 8, 8)
        hc_layout.setSpacing(5)

        hist_header = QHBoxLayout()
        lbl_hist = QLabel("Saved Scan History")
        lbl_hist.setObjectName("SectionTitle")
        hist_header.addWidget(lbl_hist)
        hist_header.addStretch()
        btn_reset_chat = QPushButton("Reset AI")
        btn_reset_chat.setToolTip("Reset AI conversation context")
        btn_reset_chat.clicked.connect(self.reset_ai_context)
        hist_header.addWidget(btn_reset_chat)
        hc_layout.addLayout(hist_header)

        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(70)
        self.history_list.itemClicked.connect(self._on_history_clicked)
        hc_layout.addWidget(self.history_list, 1)

        left_layout.addWidget(hist_card, 1)

        # ================= RIGHT PANE: Output, Findings & Notes =================
        right_widget = QWidget()
        right_widget.setMinimumWidth(420)
        self.right_widget = right_widget
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(6)

        # Inline Approval Banner
        self.approval_bar = QFrame()
        self.approval_bar.setObjectName("ApprovalBar")
        ab_layout = QHBoxLayout(self.approval_bar)
        ab_layout.setContentsMargins(10, 8, 10, 8)
        self.approval_label = QLabel("Tool confirmation required")
        self.approval_label.setWordWrap(True)
        self.approval_label.setStyleSheet("color: #f0f6fc; font-weight: 600;")
        ab_layout.addWidget(self.approval_label, 1)

        self.btn_approve = QPushButton("✓ Approve")
        self.btn_approve.setObjectName("PrimaryBtn")
        self.btn_approve.clicked.connect(lambda: self._respond_approval(True))
        self.btn_decline = QPushButton("✗ Decline")
        self.btn_decline.setObjectName("DangerBtn")
        self.btn_decline.clicked.connect(lambda: self._respond_approval(False))
        ab_layout.addWidget(self.btn_approve)
        ab_layout.addWidget(self.btn_decline)
        self.approval_bar.hide()
        right_layout.addWidget(self.approval_bar)

        self.right_tabs = QTabWidget()
        right_layout.addWidget(self.right_tabs, 1)

        # --- TAB 1: Live Output & Streaming AI ---
        live_tab = QWidget()
        live_layout = QVBoxLayout(live_tab)
        live_layout.setContentsMargins(0, 4, 0, 0)

        output_splitter = QSplitter(Qt.Orientation.Vertical)
        live_layout.addWidget(output_splitter, 1)

        raw_card = QFrame()
        raw_card.setObjectName("PanelCard")
        raw_layout = QVBoxLayout(raw_card)
        raw_layout.setSpacing(6)

        raw_hdr = QHBoxLayout()
        raw_hdr.setSpacing(6)
        lbl_raw = QLabel("Raw Tool Output")
        lbl_raw.setObjectName("SectionTitle")
        lbl_raw.setToolTip("Raw Tool Output / Terminal Log")
        raw_hdr.addWidget(lbl_raw)
        raw_hdr.addStretch()

        self.btn_analyze_raw = QPushButton("🤖 Analyze")
        self.btn_analyze_raw.setToolTip("Analyze current raw output with AI")
        self.btn_analyze_raw.clicked.connect(self.analyze_current_raw_output)
        btn_copy_raw = QPushButton("Copy")
        btn_copy_raw.clicked.connect(lambda: self._copy_text(self.raw_output.toPlainText()))
        btn_save_raw = QPushButton("Save .txt")
        btn_save_raw.clicked.connect(lambda: self._save_text(self.raw_output.toPlainText(), "scan-output.txt"))
        btn_clear_raw = QPushButton("Clear")
        btn_clear_raw.clicked.connect(self.clear_raw_output)

        raw_hdr.addWidget(self.btn_analyze_raw)
        raw_hdr.addWidget(btn_copy_raw)
        raw_hdr.addWidget(btn_save_raw)
        raw_hdr.addWidget(btn_clear_raw)
        raw_layout.addLayout(raw_hdr)

        self.raw_output = QTextEdit()
        self.raw_output.setObjectName("RawOutput")
        self.raw_output.setReadOnly(True)
        self.raw_output.setPlaceholderText("Live raw stdout/stderr from Kali tools appears here...")
        raw_layout.addWidget(self.raw_output, 1)

        ai_card = QFrame()
        ai_card.setObjectName("PanelCard")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(6)

        ai_hdr = QHBoxLayout()
        ai_hdr.setSpacing(6)
        lbl_ai = QLabel("AI Analysis (Live)")
        lbl_ai.setObjectName("SectionTitle")
        lbl_ai.setToolTip("AI Analysis & Findings (Live Streaming)")
        ai_hdr.addWidget(lbl_ai)
        ai_hdr.addStretch()

        btn_copy_ai = QPushButton("Copy")
        btn_copy_ai.clicked.connect(lambda: self._copy_text("\n\n---\n\n".join(self.ai_markdown_sections)))
        btn_save_ai = QPushButton("Save .md")
        btn_save_ai.clicked.connect(lambda: self._save_text("\n\n---\n\n".join(self.ai_markdown_sections), "analysis.md"))
        btn_clear_ai = QPushButton("Clear")
        btn_clear_ai.clicked.connect(self.clear_ai_output)

        ai_hdr.addWidget(btn_copy_ai)
        ai_hdr.addWidget(btn_save_ai)
        ai_hdr.addWidget(btn_clear_ai)
        ai_layout.addLayout(ai_hdr)

        self.ai_output = QTextBrowser()
        self.ai_output.setObjectName("AiOutput")
        self.ai_output.setOpenExternalLinks(True)
        self.ai_output.setPlaceholderText("Real-time AI analysis, attack paths, and recommendations stream here...")
        ai_layout.addWidget(self.ai_output, 1)

        output_splitter.addWidget(raw_card)
        output_splitter.addWidget(ai_card)
        output_splitter.setSizes([320, 260])

        self.right_tabs.addTab(live_tab, "📺 Live Output && AI")

        # --- TAB 2: Structured Findings & Ports Table ---
        findings_tab = QWidget()
        ft_layout = QVBoxLayout(findings_tab)
        ft_layout.setContentsMargins(0, 6, 0, 0)
        ft_layout.setSpacing(6)

        ft_toolbar = QHBoxLayout()
        ft_toolbar.setSpacing(6)
        self.findings_filter_input = QLineEdit()
        self.findings_filter_input.setMinimumWidth(110)
        self.findings_filter_input.setPlaceholderText("Filter findings (host, port, service)...")
        self.findings_filter_input.textChanged.connect(self._render_findings_table)

        self.severity_filter_combo = QComboBox()
        for s in ["All", "Critical", "High", "Medium", "Low", "Info"]:
            self.severity_filter_combo.addItem(s)
        self.severity_filter_combo.currentIndexChanged.connect(self._render_findings_table)

        self.btn_followup = QPushButton("⚡ Follow-Up")
        self.btn_followup.setToolTip("Run AI follow-up on selected finding")
        self.btn_followup.setObjectName("DirectBtn")
        self.btn_followup.clicked.connect(self.run_selected_followup)

        btn_clear_findings = QPushButton("Clear")
        btn_clear_findings.setToolTip("Clear all findings for this engagement")
        btn_clear_findings.clicked.connect(self.clear_engagement_findings)

        ft_toolbar.addWidget(self.findings_filter_input, 1)
        ft_toolbar.addWidget(self.severity_filter_combo)
        ft_toolbar.addWidget(self.btn_followup)
        ft_toolbar.addWidget(btn_clear_findings)
        ft_layout.addLayout(ft_toolbar)

        self.findings_table = QTableWidget(0, 6)
        self.findings_table.setHorizontalHeaderLabels(["Severity", "Host", "Port", "Service", "Finding", "Source"])
        self.findings_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.findings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = self.findings_table.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        ft_layout.addWidget(self.findings_table, 1)

        self.right_tabs.addTab(findings_tab, "🎯 Findings && Ports (0)")

        # --- TAB 3: Lab / CTF Notes & Report Export ---
        notes_tab = QWidget()
        nt_layout = QVBoxLayout(notes_tab)
        nt_layout.setContentsMargins(0, 6, 0, 0)
        nt_layout.setSpacing(6)

        nt_bar = QHBoxLayout()
        nt_bar.setSpacing(6)
        lbl_notes = QLabel("Lab / CTF Notes")
        lbl_notes.setObjectName("SectionTitle")
        lbl_notes.setToolTip("Lab / CTF Notes, Credentials & Flags (Auto-saved per Project)")
        nt_bar.addWidget(lbl_notes)
        nt_bar.addStretch()

        btn_save_notes = QPushButton("💾 Save")
        btn_save_notes.setToolTip("Save engagement notes")
        btn_save_notes.clicked.connect(self.save_current_notes)
        btn_export_html = QPushButton("📄 HTML")
        btn_export_html.setToolTip("Export full engagement HTML report")
        btn_export_html.setObjectName("PrimaryBtn")
        btn_export_html.clicked.connect(lambda: self.export_full_report("html"))
        btn_export_md = QPushButton("📝 Markdown")
        btn_export_md.setToolTip("Export full engagement Markdown report")
        btn_export_md.setObjectName("DirectBtn")
        btn_export_md.clicked.connect(lambda: self.export_full_report("md"))

        nt_bar.addWidget(btn_save_notes)
        nt_bar.addWidget(btn_export_html)
        nt_bar.addWidget(btn_export_md)
        nt_layout.addLayout(nt_bar)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText(
            "Track discovered flags, credentials, endpoints, pivot commands, or CTF writeup notes here..."
        )
        nt_layout.addWidget(self.notes_edit, 1)

        self.right_tabs.addTab(notes_tab, "📝 Notes && Report Export")

        self.main_splitter.addWidget(self.left_widget)
        self.main_splitter.addWidget(self.right_widget)

        self._set_status("Ready. Enter Target on the left and run AI, Direct Tool, or a Playbook.")

    # ---------------- UI Helpers ----------------
    def _set_status(self, text: str, timeout: int = 0):
        sb = self.statusBar()
        if sb is not None:
            sb.showMessage(text, timeout)

    def _toggle_advanced_box(self, checked: bool):
        self.adv_box.setVisible(checked)

    def _browse_wordlist(self):
        start_dir = "/usr/share/wordlists" if os.path.isdir("/usr/share/wordlists") else SCRIPT_DIR
        path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist", start_dir)
        if path:
            self.wordlist_input.setText(path)

    def _update_elapsed_label(self):
        if self._run_started_at is None:
            self.elapsed_lbl.setText("")
            return
        secs = int(time.time() - self._run_started_at)
        self.elapsed_lbl.setText(f"⏱ {secs // 60:02d}:{secs % 60:02d}")

    # ---------------- Provider & Server Helpers ----------------
    def _populate_models(self, cfg: Dict[str, Any]):
        models = [str(m) for m in (cfg.get("models") or [])]
        selected = str(cfg.get("model") or "")
        if selected and selected not in models:
            models.insert(0, selected)
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        if selected:
            self.model_combo.setCurrentText(selected)
        line_edit = self.model_combo.lineEdit()
        if line_edit is not None:
            line_edit.setCursorPosition(0)
        self.model_combo.blockSignals(False)

    def _select_provider(self, provider: str):
        idx = self.provider_combo.findData(provider)
        if idx >= 0:
            self.provider_combo.blockSignals(True)
            self.provider_combo.setCurrentIndex(idx)
            self.provider_combo.blockSignals(False)

    def _load_provider_defaults(self):
        cfg = resolve_provider_config()
        self._select_provider(str(cfg["provider"]))
        self._populate_models(cfg)

    def _on_provider_changed(self):
        provider = self.provider_combo.currentData()
        cfg = resolve_provider_config(provider=provider)
        self._populate_models(cfg)

    def open_api_keys_dialog(self) -> bool:
        dlg = ApiKeysDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            current_provider = self.provider_combo.currentData()
            cfg = resolve_provider_config(provider=current_provider)
            if not cfg["api_key"] and cfg["provider"] != "custom":
                cfg = resolve_provider_config()
                self._select_provider(str(cfg["provider"]))
            self._populate_models(cfg)
            if dlg.saved_path:
                self._set_status(f"API keys saved to {dlg.saved_path}", 4000)
            return True
        return False

    def refresh_server_status(self):
        health = get_kali_server_health(timeout=1.5)
        port_part = DEFAULT_KALI_SERVER_URL.rstrip("/").rsplit(":", 1)[-1]
        port_label = f":{port_part}" if port_part.isdigit() else ""
        if health.get("ok"):
            tools_map = (health.get("data") or {}).get("tools_status", {})
            ready_count = sum(1 for v in tools_map.values() if v)
            suffix = f" ({ready_count}/{len(tools_map)})" if tools_map else ""
            self.server_status_lbl.setText(f"● Running {port_label}{suffix}".strip())
            self.server_status_lbl.setStyleSheet("color: #3fb950; font-weight: 700;")
            tip = DEFAULT_KALI_SERVER_URL
            if tools_map:
                tip += "\n" + json.dumps(tools_map, indent=2)
            self.server_status_lbl.setToolTip(tip)
        else:
            self.server_status_lbl.setText(f"● Offline {port_label}".strip())
            self.server_status_lbl.setStyleSheet("color: #f85149; font-weight: 700;")
            self.server_status_lbl.setToolTip(DEFAULT_KALI_SERVER_URL)

    def run_server_action(self, action: str):
        if self.server_worker and self.server_worker.isRunning():
            return
        self._set_status(f"Running server action: {action}...")
        self.server_worker = ServerActionWorker(action)
        self.server_worker.completed.connect(self._on_server_action_done)
        self.server_worker.start()

    def _on_server_action_done(self, ok: bool, output: str):
        self.refresh_server_status()
        if output:
            self.append_raw_log(output, level="info" if ok else "error")
        self._set_status("Server command completed." if ok else "Server command failed.", 4000)

    # ---------------- Engagement / SQLite Workspace ----------------
    def _load_engagements_combo(self, select_id: Optional[int] = None):
        engagements = self.store.list_engagements()
        self.engagement_combo.blockSignals(True)
        self.engagement_combo.clear()
        target_idx = 0
        for idx, eng in enumerate(engagements):
            self.engagement_combo.addItem(eng["name"], eng["id"])
            if select_id is not None and eng["id"] == select_id:
                target_idx = idx
        self.engagement_combo.setCurrentIndex(target_idx)
        self.engagement_combo.blockSignals(False)
        if engagements:
            self._switch_to_engagement(int(self.engagement_combo.currentData()))

    def _on_engagement_changed(self):
        eng_id = self.engagement_combo.currentData()
        if eng_id is not None:
            self._switch_to_engagement(int(eng_id))

    def _switch_to_engagement(self, engagement_id: int):
        self.current_engagement_id = engagement_id
        eng = self.store.get_engagement(engagement_id)
        if not eng:
            return
        self.target_input.setText(eng.get("target", ""))
        self.notes_edit.setPlainText(eng.get("notes", ""))

        loaded_msgs = self.store.load_chat_messages(engagement_id)
        self.messages = loaded_msgs if loaded_msgs else [{"role": "system", "content": SYSTEM_PROMPT}]

        self.clear_raw_output()
        self.clear_ai_output()
        self._reload_history_from_store()
        self._reload_findings_from_store()

    def _persist_current_target(self):
        self.store.update_engagement_target(self.current_engagement_id, self.target_input.text().strip())

    def create_new_engagement(self):
        name, ok = QInputDialog.getText(self, "New Project / Lab", "Project or CTF name:")
        if ok and name.strip():
            eng = self.store.create_or_get_engagement(name.strip(), target=self.target_input.text().strip())
            self._load_engagements_combo(select_id=int(eng["id"]))

    def delete_current_engagement(self):
        if len(self.store.list_engagements()) <= 1:
            QMessageBox.information(self, "Cannot Delete", "At least one project must remain.")
            return
        ans = QMessageBox.question(
            self,
            "Delete Project",
            "Delete the selected project and all of its saved scans/findings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.store.delete_engagement(self.current_engagement_id)
            self._load_engagements_combo()

    def save_current_notes(self):
        self.store.update_engagement_notes(self.current_engagement_id, self.notes_edit.toPlainText())
        self._set_status("Lab / CTF notes saved.", 3000)

    def _reload_history_from_store(self):
        self.history_entries = self.store.list_scans(self.current_engagement_id)
        self.history_list.clear()
        for idx, entry in enumerate(self.history_entries):
            item = QListWidgetItem(f"[{entry['created_at'][11:]}] {entry['title']}")
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.history_list.addItem(item)

    def _reload_findings_from_store(self):
        self.current_findings = self.store.list_findings(self.current_engagement_id)
        self._render_findings_table()

    def _render_findings_table(self):
        query = self.findings_filter_input.text().strip().lower()
        sev_filter = self.severity_filter_combo.currentText()
        sev_colors = {
            "Critical": "#f85149",
            "High": "#db6d28",
            "Medium": "#d29922",
            "Low": "#58a6ff",
            "Info": "#8b949e",
        }

        filtered: List[Dict[str, Any]] = []
        for f in self.current_findings:
            if sev_filter != "All" and f.get("severity") != sev_filter:
                continue
            blob = " ".join(
                str(f.get(k, "")) for k in ("severity", "host", "port", "service", "title", "details", "source_tool")
            ).lower()
            if query and query not in blob:
                continue
            filtered.append(f)

        self.findings_table.setRowCount(len(filtered))
        for row_idx, f in enumerate(filtered):
            sev = str(f.get("severity", "Info"))
            sev_item = QTableWidgetItem(sev)
            sev_item.setForeground(QColor(sev_colors.get(sev, "#e6edf3")))
            sev_item.setData(Qt.ItemDataRole.UserRole, f)

            self.findings_table.setItem(row_idx, 0, sev_item)
            self.findings_table.setItem(row_idx, 1, QTableWidgetItem(str(f.get("host", "-"))))
            self.findings_table.setItem(row_idx, 2, QTableWidgetItem(str(f.get("port", "-"))))
            self.findings_table.setItem(row_idx, 3, QTableWidgetItem(str(f.get("service", "-"))))
            title_item = QTableWidgetItem(str(f.get("title", "")))
            title_item.setToolTip(str(f.get("details", "")))
            self.findings_table.setItem(row_idx, 4, title_item)
            self.findings_table.setItem(row_idx, 5, QTableWidgetItem(str(f.get("source_tool", "-"))))

        self.right_tabs.setTabText(1, f"🎯 Findings && Ports ({len(self.current_findings)})")

    def clear_engagement_findings(self):
        self.store.clear_findings(self.current_engagement_id)
        self._reload_findings_from_store()

    # ---------------- Output Formatting & Streaming ----------------
    def append_raw_log(self, text: str, level: str = "stdout"):
        if not text:
            return
        color_map = {
            "cmd": "#58a6ff",
            "stdout": "#e6edf3",
            "stderr": "#f85149",
            "error": "#f85149",
            "info": "#8b949e",
            "success": "#3fb950",
        }
        color = color_map.get(level, "#e6edf3")
        escaped = html.escape(text).replace("\n", "<br>")
        self.raw_output.moveCursor(QTextCursor.MoveOperation.End)
        self.raw_output.insertHtml(f'<span style="color:{color}; white-space:pre-wrap;">{escaped}</span><br>')
        self.raw_output.moveCursor(QTextCursor.MoveOperation.End)
        self.raw_log_plain += text + "\n"

    def append_ai_delta(self, chunk: str):
        if self._streaming_section_index is None:
            self._streaming_buffer = chunk
            self.ai_markdown_sections.append(self._streaming_buffer)
            self._streaming_section_index = len(self.ai_markdown_sections) - 1
        else:
            self._streaming_buffer += chunk
            self.ai_markdown_sections[self._streaming_section_index] = self._streaming_buffer
        self._render_ai_markdown()

    def append_ai_section(self, markdown_text: str):
        if self._streaming_section_index is not None:
            self.ai_markdown_sections[self._streaming_section_index] = markdown_text
            self._streaming_section_index = None
            self._streaming_buffer = ""
        else:
            self.ai_markdown_sections.append(markdown_text)
        self._render_ai_markdown()

    def _render_ai_markdown(self):
        combined = "\n\n---\n\n".join(self.ai_markdown_sections)
        self.ai_output.setMarkdown(combined)
        sb = self.ai_output.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def clear_raw_output(self):
        self.raw_output.clear()
        self.raw_log_plain = ""

    def clear_ai_output(self):
        self.ai_output.clear()
        self.ai_markdown_sections.clear()
        self._streaming_section_index = None
        self._streaming_buffer = ""

    def _copy_text(self, text: str):
        if not text.strip():
            return
        QApplication.clipboard().setText(text)
        self._set_status("Copied to clipboard.", 3000)

    def _save_text(self, text: str, default_name: str):
        if not text.strip():
            QMessageBox.information(self, "Nothing to Save", "Output is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Output", os.path.join(SCRIPT_DIR, default_name))
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self._set_status(f"Saved to {path}", 4000)

    def export_full_report(self, fmt: str):
        self.save_current_notes()
        eng = self.store.get_engagement(self.current_engagement_id) or {"name": "Lab / CTF", "target": "", "notes": ""}
        scans = self.store.list_scans(self.current_engagement_id)
        findings = self.store.list_findings(self.current_engagement_id)
        ai_summary = "\n\n---\n\n".join(self.ai_markdown_sections)

        ext = "html" if fmt == "html" else "md"
        default_file = os.path.join(SCRIPT_DIR, f"kali-report.{ext}")
        path, _ = QFileDialog.getSaveFileName(self, f"Export {ext.upper()} Report", default_file)
        if not path:
            return
        content = (
            generate_html_report(eng, findings, scans, ai_summary)
            if fmt == "html"
            else generate_markdown_report(eng, findings, scans, ai_summary)
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        self._set_status(f"Exported report to {path}", 5000)

    # ---------------- Presets & History ----------------
    def apply_preset(self, tool_key: str, template: str):
        target = self.target_input.text().strip() or "<target>"
        self.prompt_input.setPlainText(template.format(target=target))
        idx = self.direct_tool_combo.findData(tool_key)
        if idx >= 0:
            self.direct_tool_combo.setCurrentIndex(idx)

    def _save_history_snapshot(self, label: str, tool_name: str, target: str):
        raw_text = self.raw_output.toPlainText()
        ai_text = "\n\n---\n\n".join(self.ai_markdown_sections)
        parsed = [f.to_dict() for f in parse_tool_output(tool_name, raw_text, target)]
        self.store.save_scan_and_findings(
            engagement_id=self.current_engagement_id,
            title=f"{label} — {target}",
            tool_name=tool_name,
            target=target,
            raw_output=raw_text,
            ai_analysis=ai_text,
            findings=parsed,
        )
        self._reload_history_from_store()
        self._reload_findings_from_store()

    def _on_history_clicked(self, item: QListWidgetItem):
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is None or not (0 <= idx < len(self.history_entries)):
            return
        entry = self.history_entries[idx]
        self.target_input.setText(entry["target"])
        self.clear_raw_output()
        if entry["raw_output"]:
            self.append_raw_log(entry["raw_output"], level="stdout")
        self.clear_ai_output()
        if entry["ai_analysis"]:
            self.ai_markdown_sections = [entry["ai_analysis"]]
            self._render_ai_markdown()
        self.right_tabs.setCurrentIndex(0)

    def reset_ai_context(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.store.save_chat_messages(self.current_engagement_id, self.messages)
        self.clear_ai_output()
        self._set_status("AI conversation context reset.", 3000)

    # ---------------- Execution Controls ----------------
    def _set_running_state(self, running: bool):
        self.btn_run_ai.setEnabled(not running)
        self.btn_run_direct.setEnabled(not running)
        self.btn_analyze_raw.setEnabled(not running)
        self.btn_pb_web.setEnabled(not running)
        self.btn_pb_net.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        if running:
            self._run_started_at = time.time()
            self.elapsed_timer.start(1000)
            self._update_elapsed_label()
        else:
            self.elapsed_timer.stop()
            self._run_started_at = None
            self.elapsed_lbl.setText("")

    def _ensure_server_ready(self) -> bool:
        if get_kali_server_health(timeout=1.5).get("ok"):
            return True
        ans = QMessageBox.question(
            self,
            "Kali Server Offline",
            "kali-server-mcp is not running on 127.0.0.1:5000.\nStart it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            proc = subprocess.run([MANAGER_SCRIPT, "start"], capture_output=True, text=True, timeout=15)
            self.refresh_server_status()
            if proc.stdout:
                self.append_raw_log(proc.stdout.strip(), level="info")
            return bool(get_kali_server_health(timeout=2.0).get("ok"))
        return False

    def run_ai_scan(self):
        if self.current_worker and self.current_worker.isRunning():
            return

        target = self.target_input.text().strip()
        prompt_text = self.prompt_input.toPlainText().strip()
        if not target and not prompt_text:
            QMessageBox.warning(self, "Missing Input", "Enter a Target or AI Prompt in the left pane.")
            return

        self._persist_current_target()
        provider = self.provider_combo.currentData()
        model = self.model_combo.currentText().strip()
        cfg = resolve_provider_config(provider=provider, model=model or None)
        if not cfg["api_key"] and cfg["provider"] != "custom":
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Missing API Key")
            msg_box.setText(
                f"No API key configured for {cfg['provider_label']} ({cfg['env_key']})."
            )
            msg_box.setInformativeText("Open the API Keys Manager to add your key now?")
            btn_open = msg_box.addButton("🔑 Open API Keys", QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton(QMessageBox.StandardButton.Cancel)
            msg_box.exec()
            if msg_box.clickedButton() == btn_open and self.open_api_keys_dialog():
                provider = self.provider_combo.currentData()
                model = self.model_combo.currentText().strip()
                cfg = resolve_provider_config(provider=provider, model=model or None)
                if not cfg["api_key"] and cfg["provider"] != "custom":
                    return
            else:
                return

        if not self._ensure_server_ready():
            return

        if target and prompt_text:
            full_prompt = prompt_text if target in prompt_text else f"Target: {target}\nTask: {prompt_text}"
        elif target:
            full_prompt = f"Analyze and perform initial reconnaissance on target: {target}. Summarize findings clearly."
        else:
            full_prompt = prompt_text

        ts = datetime.now().strftime("%H:%M:%S")
        self.append_raw_log(f"\n=== [{ts}] AI Task | Target: {target or 'N/A'} ===", level="cmd")
        self.append_ai_section(f"**User ({ts}):** {full_prompt}")
        self._streaming_section_index = None
        self._streaming_buffer = ""

        self.messages.append({"role": "user", "content": full_prompt})
        self._set_running_state(True)
        self.right_tabs.setCurrentIndex(0)
        self._set_status(f"Streaming AI ({cfg['provider_label']}: {cfg['model']})...")

        worker = AgentWorker(
            provider=str(cfg["provider"]),
            model=str(cfg["model"]),
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            messages=self.messages,
            auto_approve=self.auto_approve_chk.isChecked(),
        )
        worker.reasoning_received.connect(lambda r: self.append_raw_log(f"[AI Reasoning]\n{r}", level="info"))
        worker.assistant_delta.connect(self.append_ai_delta)
        worker.assistant_received.connect(self.append_ai_section)
        worker.tool_planned.connect(self._on_tool_planned)
        worker.approval_requested.connect(self._on_approval_requested)
        worker.tool_executing.connect(lambda name, _args: self.append_raw_log(f"[*] Executing {name}...", level="info"))
        worker.tool_result_received.connect(lambda name, res: self._on_tool_result(name, res, target or "Prompt"))
        worker.error_received.connect(lambda etype, msg: self.append_raw_log(f"[!] {etype.upper()} Error: {msg}", level="error"))
        worker.finished_turn.connect(lambda updated_msgs: self._on_ai_finished(updated_msgs, target or "Prompt"))
        self.current_worker = worker
        worker.start()

    def _build_direct_tool_call(self, tool_key: str, target: str, prompt_text: str) -> Optional[tuple[str, Dict[str, Any]]]:
        ports = self.ports_input.text().strip()
        extra_flags = self.flags_input.text().strip()
        wordlist = self.wordlist_input.text().strip() or "/usr/share/wordlists/dirb/common.txt"

        if tool_key == "execute_command":
            if not prompt_text:
                QMessageBox.warning(self, "Missing Command", "Enter a shell command in the Prompt box.")
                return None
            return ("execute_command", {"command": prompt_text})

        if not target:
            QMessageBox.warning(self, "Missing Target", "Enter a Target IP, domain, or URL.")
            return None

        if tool_key == "tls_dns":
            host = target.replace("https://", "").replace("http://", "").split("/")[0]
            qhost = shlex.quote(host)
            cmd = (
                f"echo | openssl s_client -connect {qhost}:443 -servername {qhost} 2>&1 | head -n 65; "
                f"echo '--- DNS ---'; dig +short {qhost} A {qhost} NS {qhost} TXT"
            )
            return ("execute_command", {"command": cmd})

        if tool_key == "searchsploit":
            return ("execute_command", {"command": f"searchsploit --json {shlex.quote(target)}"})

        url = target if target.startswith(("http://", "https://")) else f"http://{target}"
        if tool_key == "nmap_scan":
            return ("nmap_scan", {"target": target, "scan_type": "-sCV", "ports": ports, "additional_args": extra_flags or "-T4"})
        if tool_key == "nikto_scan":
            return ("nikto_scan", {"target": target, "additional_args": extra_flags})
        if tool_key == "gobuster_scan":
            return ("gobuster_scan", {"url": url, "mode": "dir", "wordlist": wordlist, "additional_args": extra_flags})
        if tool_key == "dirb_scan":
            return ("dirb_scan", {"url": url, "wordlist": wordlist, "additional_args": extra_flags})
        if tool_key == "sqlmap_scan":
            return ("sqlmap_scan", {"url": url, "additional_args": extra_flags})
        if tool_key == "wpscan_analyze":
            return ("wpscan_analyze", {"url": url, "additional_args": extra_flags or "--enumerate vp,u"})
        if tool_key == "enum4linux_scan":
            return ("enum4linux_scan", {"target": target, "additional_args": extra_flags or "-a"})
        return (tool_key, {"target": target})

    def run_direct_tool(self):
        if self.current_worker and self.current_worker.isRunning():
            return

        tool_key = str(self.direct_tool_combo.currentData())
        target = self.target_input.text().strip()
        prompt_text = self.prompt_input.toPlainText().strip()
        built = self._build_direct_tool_call(tool_key, target, prompt_text)
        if not built:
            return
        api_tool, tool_args = built

        if not self._ensure_server_ready():
            return

        self._persist_current_target()
        ts = datetime.now().strftime("%H:%M:%S")
        self.append_raw_log(f"\n=== [{ts}] Direct: {tool_key} | {json.dumps(tool_args)} ===", level="cmd")
        self._set_running_state(True)
        self.right_tabs.setCurrentIndex(0)
        self._set_status(f"Executing {tool_key} directly on Kali server...")

        worker = DirectToolWorker(api_tool, tool_args)
        worker.tool_result_received.connect(lambda _name, res: self._on_tool_result(tool_key, res, target or "Command"))
        worker.finished_direct.connect(lambda: self._on_direct_finished(tool_key, target or "Command"))
        self.current_worker = worker
        worker.start()

    def run_playbook(self, playbook_key: str):
        if self.current_worker and self.current_worker.isRunning():
            return
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Missing Target", "Enter a Target before running a Playbook.")
            return
        if not self._ensure_server_ready():
            return

        self._persist_current_target()
        pb = PLAYBOOKS[playbook_key]
        steps = pb["steps"]
        self.playbook_progress.setMaximum(len(steps))
        self.playbook_progress.setValue(0)
        self.playbook_progress.show()

        self.append_raw_log(f"\n=== Playbook: {pb['name']} | Target: {target} ===", level="cmd")
        self._set_running_state(True)
        self.right_tabs.setCurrentIndex(0)

        worker = PlaybookWorker(
            target=target,
            steps=steps,
            wordlist=self.wordlist_input.text().strip(),
            extra_args=self.flags_input.text().strip(),
        )
        worker.step_progress.connect(self._on_playbook_step)
        worker.tool_result_received.connect(lambda tname, res: self._on_tool_result(tname, res, target))
        worker.finished_playbook.connect(lambda ok, summary: self._on_playbook_finished(pb["name"], target, ok, summary))
        self.current_worker = worker
        worker.start()

    def _on_playbook_step(self, step_idx: int, total: int, label: str):
        self.playbook_progress.setValue(step_idx)
        self.playbook_progress.setFormat(f"Step {step_idx}/{total}: {label}")
        self.append_raw_log(f"\n[*] Playbook Step {step_idx}/{total}: {label}...", level="info")
        self._set_status(f"Playbook Step {step_idx}/{total}: {label}...")

    def _on_playbook_finished(self, pb_name: str, target: str, ok: bool, summary: str):
        self.playbook_progress.hide()
        self._set_running_state(False)
        self._save_history_snapshot(pb_name, "execute_command", target)
        if ok:
            self._set_status(f"{pb_name} finished. Click 'Analyze Output with AI' for triage.", 5000)
        else:
            self._set_status(summary, 4000)

    def run_selected_followup(self):
        row = self.findings_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Row Selected", "Select a finding row in the table first.")
            return
        sev_item = self.findings_table.item(row, 0)
        if sev_item is None:
            return
        f = sev_item.data(Qt.ItemDataRole.UserRole) or {}
        tool = f.get("follow_up_tool") or "nikto_scan"
        target = f.get("follow_up_target") or f.get("host") or self.target_input.text().strip()
        if not target:
            return
        self.target_input.setText(str(target))
        idx = self.direct_tool_combo.findData(tool)
        if idx >= 0:
            self.direct_tool_combo.setCurrentIndex(idx)
        self.run_direct_tool()

    def analyze_current_raw_output(self):
        raw_text = self.raw_output.toPlainText().strip()
        if not raw_text:
            QMessageBox.information(self, "No Output", "No raw output available to analyze.")
            return
        target = self.target_input.text().strip() or "current target"
        snippet = raw_text[-12000:]
        self.prompt_input.setPlainText(
            f"Analyze this scan output for {target}. Highlight open services, security issues, potential exploits, and next steps:\n\n{snippet}"
        )
        self.run_ai_scan()

    def stop_current_run(self):
        if isinstance(self.current_worker, (AgentWorker, DirectToolWorker, PlaybookWorker)):
            self.current_worker.request_stop()
        self.approval_bar.hide()
        self.playbook_progress.hide()
        self.append_raw_log("[!] Stop requested by user.", level="error")
        self._set_status("Stopping active task...")

    def _on_tool_planned(self, fn_name: str, _fn_args: Dict[str, Any], cmd_preview: str):
        self._streaming_section_index = None
        self._streaming_buffer = ""
        self.append_raw_log(f"\n[ACTION] {fn_name}: {cmd_preview}", level="cmd")

    def _on_approval_requested(self, fn_name: str, _fn_args: Dict[str, Any], cmd_preview: str):
        self.approval_label.setText(f"Approve tool '{fn_name}'?\n{cmd_preview}")
        self.approval_bar.show()
        self._set_status(f"Waiting for approval: {fn_name}")

    def _respond_approval(self, approved: bool):
        self.approval_bar.hide()
        if isinstance(self.current_worker, AgentWorker):
            self.current_worker.provide_approval(approved)
        self.append_raw_log("[✓] Approved." if approved else "[✗] Declined by user.", level="success" if approved else "error")

    def _on_tool_result(self, fn_name: str, raw_result: Dict[str, Any], target_label: str):
        stdout = (raw_result.get("stdout") or "").strip()
        stderr = (raw_result.get("stderr") or "").strip()
        err = raw_result.get("error")

        if stdout:
            self.append_raw_log(stdout, level="stdout")
            parsed = [f.to_dict() for f in parse_tool_output(fn_name, stdout, target_label)]
            if parsed:
                self.current_findings.extend(parsed)
                self._render_findings_table()
        if stderr:
            self.append_raw_log(f"[stderr]\n{stderr}", level="stderr")
        if err and not stderr:
            self.append_raw_log(f"[error] {err}", level="error")
        if not stdout and not stderr and not err:
            self.append_raw_log(f"[{fn_name}] Completed: {json.dumps(raw_result)}", level="info")

    def _on_ai_finished(self, updated_messages: List[Dict[str, Any]], label_target: str):
        self.messages = updated_messages
        self.store.save_chat_messages(self.current_engagement_id, self.messages)
        self._streaming_section_index = None
        self._streaming_buffer = ""
        self.approval_bar.hide()
        self._set_running_state(False)
        self._save_history_snapshot("AI Scan", "execute_command", label_target)
        self._set_status("AI task finished.", 4000)

    def _on_direct_finished(self, tool_name: str, label_target: str):
        self._set_running_state(False)
        self._save_history_snapshot(tool_name, tool_name, label_target)
        self._set_status(f"Direct {tool_name} finished.", 4000)

    def closeEvent(self, event):
        self.save_current_notes()
        if isinstance(self.current_worker, (AgentWorker, DirectToolWorker, PlaybookWorker)) and self.current_worker.isRunning():
            self.current_worker.request_stop()
            self.current_worker.wait(1500)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = KaliGuiWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
