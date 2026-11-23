#!/usr/bin/env python3
"""
Kali MCP Desktop GUI
--------------------
Side-by-side PySide6 GUI for Kali Linux MCP:
- Left pane: Target input, quick scan presets, AI prompt, provider/server controls, and scan history.
- Right pane: Instant live raw tool output (top) and AI analysis/findings (bottom), plus inline tool approval.
"""

import html
import json
import os
import shlex
import subprocess
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kali_core import (
    AgentCallbacks,
    DEFAULT_KALI_SERVER_URL,
    SYSTEM_PROMPT,
    call_kali_api,
    create_openai_client,
    get_kali_server_health,
    resolve_provider_config,
    run_chat_turn,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGER_SCRIPT = os.path.join(SCRIPT_DIR, "kali-mcp-manager.sh")

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
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
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLineEdit, QPlainTextEdit, QComboBox, QListWidget {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #1f6feb;
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
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
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
    padding: 5px 8px;
    font-size: 12px;
}
QPushButton#PresetBtn:hover {
    border-color: #58a6ff;
    color: #58a6ff;
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
    """Runs an AI agent chat turn in a background thread."""

    reasoning_received = Signal(str)
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

    def request_stop(self):
        self._stop_requested = True
        self._approval_result = False
        self._approval_event.set()

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

        callbacks = AgentCallbacks(
            on_reasoning=lambda text: self.reasoning_received.emit(text),
            on_assistant_message=lambda text: self.assistant_received.emit(text),
            on_tool_planned=lambda name, args, prev: self.tool_planned.emit(name, args, prev),
            on_confirm=on_confirm,
            on_tool_executing=lambda name, args: self.tool_executing.emit(name, args),
            on_tool_result=lambda name, res: self.tool_result_received.emit(name, res),
            on_error=lambda etype, msg: self.error_received.emit(etype, msg),
            should_stop=lambda: self._stop_requested,
        )

        run_chat_turn(
            client=client,
            model=self.model,
            messages=self.messages,
            auto_approve=self.auto_approve,
            callbacks=callbacks,
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

    def run(self):
        result = call_kali_api(self.tool_name, self.tool_args)
        self.tool_result_received.emit(self.tool_name, result)
        self.finished_direct.emit()


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


class KaliGuiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kali MCP AI & Pentest GUI")
        self.resize(1380, 840)

        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.history_entries: List[Dict[str, str]] = []
        self.raw_log_plain = ""
        self.ai_markdown_sections: List[str] = []
        self.current_worker: Optional[QThread] = None
        self.server_worker: Optional[ServerActionWorker] = None

        self._build_ui()
        self.setStyleSheet(DARK_STYLESHEET)
        self._load_provider_defaults()
        self.refresh_server_status()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_server_status)
        self.status_timer.start(10000)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        # --- Top Bar ---
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(10)

        title_lbl = QLabel("KALI MCP AI WORKBENCH")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #58a6ff; letter-spacing: 0.8px;")
        top_layout.addWidget(title_lbl)

        self.server_status_lbl = QLabel("● Checking server...")
        self.server_status_lbl.setStyleSheet("color: #d29922; font-weight: 600;")
        top_layout.addWidget(self.server_status_lbl)

        self.btn_start_srv = QPushButton("Start")
        self.btn_start_srv.clicked.connect(lambda: self.run_server_action("start"))
        self.btn_restart_srv = QPushButton("Restart")
        self.btn_restart_srv.clicked.connect(lambda: self.run_server_action("restart"))
        self.btn_stop_srv = QPushButton("Stop")
        self.btn_stop_srv.clicked.connect(lambda: self.run_server_action("stop"))
        top_layout.addWidget(self.btn_start_srv)
        top_layout.addWidget(self.btn_restart_srv)
        top_layout.addWidget(self.btn_stop_srv)

        top_layout.addStretch()

        top_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("NVIDIA NIM", "nvidia")
        self.provider_combo.addItem("OpenAI", "openai")
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        top_layout.addWidget(self.provider_combo)

        top_layout.addWidget(QLabel("Model:"))
        self.model_input = QLineEdit()
        self.model_input.setMinimumWidth(290)
        top_layout.addWidget(self.model_input)

        root_layout.addWidget(top_bar)

        # --- Main Side-by-Side Splitter ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(main_splitter, 1)

        # ================= LEFT PANE: Target & Controls =================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(10)

        target_card = QFrame()
        target_card.setObjectName("PanelCard")
        tc_layout = QVBoxLayout(target_card)
        tc_layout.setSpacing(8)

        lbl_target = QLabel("Target (IP / Domain / URL)")
        lbl_target.setObjectName("SectionTitle")
        tc_layout.addWidget(lbl_target)

        self.target_input = QLineEdit()
        self.target_input.setObjectName("TargetInput")
        self.target_input.setPlaceholderText("e.g. 127.0.0.1, dictionary.com, https://example.com")
        self.target_input.returnPressed.connect(self.run_ai_scan)
        tc_layout.addWidget(self.target_input)

        lbl_presets = QLabel("Quick Presets (One-Click Fill)")
        lbl_presets.setObjectName("SectionTitle")
        tc_layout.addWidget(lbl_presets)

        preset_grid = QGridLayout()
        preset_grid.setSpacing(6)
        presets = [
            ("Nmap (-sCV)", "nmap", "Run an Nmap -sCV -T4 port and service scan on {target} and summarize open ports and risks."),
            ("Full Recon", "recon", "Perform reconnaissance on {target}: scan common ports with nmap, check HTTP headers, and inspect TLS/DNS info."),
            ("Nikto Web", "nikto", "Run a Nikto web vulnerability scan against {target} and summarize findings."),
            ("Gobuster Dir", "gobuster", "Run Gobuster directory enumeration on {target} using common.txt and report discovered paths."),
            ("SQLmap", "sqlmap", "Check {target} with SQLmap (--batch) and report any potential SQL injection points."),
            ("TLS / DNS Info", "tls_dns", "Run openssl s_client certificate/TLS check and dig DNS records on {target}, then summarize security posture."),
        ]
        for idx, (label, tool_key, template) in enumerate(presets):
            btn = QPushButton(label)
            btn.setObjectName("PresetBtn")
            btn.clicked.connect(lambda _=False, k=tool_key, t=template: self.apply_preset(k, t))
            preset_grid.addWidget(btn, idx // 3, idx % 3)
        tc_layout.addLayout(preset_grid)

        lbl_prompt = QLabel("AI Prompt / Custom Command")
        lbl_prompt.setObjectName("SectionTitle")
        tc_layout.addWidget(lbl_prompt)

        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlaceholderText(
            "Ilagay dito ang gusto mong ipagawa sa AI (hal. 'Scan open ports and check SSL cert'). "
            "Kapag blanko at nag-Run with AI, gagawa ng general recon sa Target."
        )
        self.prompt_input.setMinimumHeight(95)
        self.prompt_input.setMaximumHeight(150)
        tc_layout.addWidget(self.prompt_input)

        direct_row = QHBoxLayout()
        direct_row.addWidget(QLabel("Direct Tool:"))
        self.direct_tool_combo = QComboBox()
        self.direct_tool_combo.addItem("nmap_scan (-sCV -T4)", "nmap_scan")
        self.direct_tool_combo.addItem("nikto_scan", "nikto_scan")
        self.direct_tool_combo.addItem("gobuster_scan (dir)", "gobuster_scan")
        self.direct_tool_combo.addItem("sqlmap_scan (--batch)", "sqlmap_scan")
        self.direct_tool_combo.addItem("TLS + DNS (openssl/dig)", "tls_dns")
        self.direct_tool_combo.addItem("Custom Shell (Prompt Box)", "execute_command")
        direct_row.addWidget(self.direct_tool_combo, 1)
        tc_layout.addLayout(direct_row)

        self.auto_approve_chk = QCheckBox("Auto-approve tool calls (walang confirmation prompt)")
        self.auto_approve_chk.setChecked(False)
        tc_layout.addWidget(self.auto_approve_chk)

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

        left_layout.addWidget(target_card)

        # History Card
        hist_card = QFrame()
        hist_card.setObjectName("PanelCard")
        hc_layout = QVBoxLayout(hist_card)
        hc_layout.setSpacing(6)

        hist_header = QHBoxLayout()
        lbl_hist = QLabel("Recent Scans / History")
        lbl_hist.setObjectName("SectionTitle")
        hist_header.addWidget(lbl_hist)
        hist_header.addStretch()
        btn_reset_chat = QPushButton("Reset AI Context")
        btn_reset_chat.clicked.connect(self.reset_ai_context)
        hist_header.addWidget(btn_reset_chat)
        hc_layout.addLayout(hist_header)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self._on_history_clicked)
        hc_layout.addWidget(self.history_list, 1)

        left_layout.addWidget(hist_card, 1)

        # ================= RIGHT PANE: Output & AI Analysis =================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 0, 0, 0)
        right_layout.setSpacing(8)

        # Inline Approval Banner (shown only when manual tool confirmation is needed)
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

        # Vertical splitter inside right pane so Raw Output & AI Analysis are both visible at once
        output_splitter = QSplitter(Qt.Orientation.Vertical)
        right_layout.addWidget(output_splitter, 1)

        # Top-Right: Raw Tool Output
        raw_card = QFrame()
        raw_card.setObjectName("PanelCard")
        raw_layout = QVBoxLayout(raw_card)
        raw_layout.setSpacing(6)

        raw_hdr = QHBoxLayout()
        lbl_raw = QLabel("Raw Tool Output / Terminal Log")
        lbl_raw.setObjectName("SectionTitle")
        raw_hdr.addWidget(lbl_raw)
        raw_hdr.addStretch()

        self.btn_analyze_raw = QPushButton("🤖 Analyze Output with AI")
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
        self.raw_output.setPlaceholderText("Lalabas dito agad ang raw stdout/stderr mula sa mga Kali tools (nmap, nikto, gobuster, openssl, atbp.)...")
        raw_layout.addWidget(self.raw_output, 1)

        # Bottom-Right: AI Analysis & Findings
        ai_card = QFrame()
        ai_card.setObjectName("PanelCard")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(6)

        ai_hdr = QHBoxLayout()
        lbl_ai = QLabel("AI Analysis & Findings")
        lbl_ai.setObjectName("SectionTitle")
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
        self.ai_output.setPlaceholderText("Lalabas dito ang malinaw na buod, findings, at rekomendasyon ng AI...")
        ai_layout.addWidget(self.ai_output, 1)

        output_splitter.addWidget(raw_card)
        output_splitter.addWidget(ai_card)
        output_splitter.setSizes([430, 330])

        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([460, 900])

        self.statusBar().showMessage("Ready. Ilagay ang Target sa kaliwa at pindutin ang Run.")

    # ---------------- Provider & Server Helpers ----------------
    def _load_provider_defaults(self):
        cfg = resolve_provider_config()
        idx = self.provider_combo.findData(cfg["provider"])
        if idx >= 0:
            self.provider_combo.blockSignals(True)
            self.provider_combo.setCurrentIndex(idx)
            self.provider_combo.blockSignals(False)
        self.model_input.setText(cfg["model"])

    def _on_provider_changed(self):
        provider = self.provider_combo.currentData()
        cfg = resolve_provider_config(provider=provider)
        self.model_input.setText(cfg["model"])

    def refresh_server_status(self):
        health = get_kali_server_health(timeout=1.5)
        if health.get("ok"):
            self.server_status_lbl.setText(f"● Running ({DEFAULT_KALI_SERVER_URL})")
            self.server_status_lbl.setStyleSheet("color: #3fb950; font-weight: 700;")
        else:
            self.server_status_lbl.setText("● Offline (127.0.0.1:5000)")
            self.server_status_lbl.setStyleSheet("color: #f85149; font-weight: 700;")

    def run_server_action(self, action: str):
        if self.server_worker and self.server_worker.isRunning():
            return
        self.statusBar().showMessage(f"Running server action: {action}...")
        self.server_worker = ServerActionWorker(action)
        self.server_worker.completed.connect(self._on_server_action_done)
        self.server_worker.start()

    def _on_server_action_done(self, ok: bool, output: str):
        self.refresh_server_status()
        if output:
            self.append_raw_log(output, level="info" if ok else "error")
        self.statusBar().showMessage("Server command completed." if ok else "Server command failed.")

    # ---------------- Output Formatting Helpers ----------------
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

    def append_ai_section(self, markdown_text: str):
        self.ai_markdown_sections.append(markdown_text)
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

    def _copy_text(self, text: str):
        if not text.strip():
            return
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Copied to clipboard.", 3000)

    def _save_text(self, text: str, default_name: str):
        if not text.strip():
            QMessageBox.information(self, "Nothing to Save", "Walang laman ang output na ise-save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Output", os.path.join(SCRIPT_DIR, default_name))
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.statusBar().showMessage(f"Saved to {path}", 4000)

    # ---------------- Presets & History ----------------
    def apply_preset(self, tool_key: str, template: str):
        target = self.target_input.text().strip() or "<target>"
        self.prompt_input.setPlainText(template.format(target=target))

        tool_map = {
            "nmap": "nmap_scan",
            "nikto": "nikto_scan",
            "gobuster": "gobuster_scan",
            "sqlmap": "sqlmap_scan",
            "tls_dns": "tls_dns",
            "recon": "nmap_scan",
        }
        mapped = tool_map.get(tool_key)
        if mapped:
            idx = self.direct_tool_combo.findData(mapped)
            if idx >= 0:
                self.direct_tool_combo.setCurrentIndex(idx)

    def _save_history_snapshot(self, label: str, target: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = {
            "title": f"[{ts}] {label} — {target}",
            "target": target,
            "raw": self.raw_output.toPlainText(),
            "ai": "\n\n---\n\n".join(self.ai_markdown_sections),
        }
        self.history_entries.insert(0, entry)
        item = QListWidgetItem(entry["title"])
        item.setData(Qt.ItemDataRole.UserRole, 0)
        self.history_list.insertItem(0, item)
        for i in range(self.history_list.count()):
            hist_item = self.history_list.item(i)
            if hist_item is not None:
                hist_item.setData(Qt.ItemDataRole.UserRole, i)

    def _on_history_clicked(self, item: QListWidgetItem):
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is None or not (0 <= idx < len(self.history_entries)):
            return
        entry = self.history_entries[idx]
        self.target_input.setText(entry["target"])
        self.clear_raw_output()
        if entry["raw"]:
            self.append_raw_log(entry["raw"], level="stdout")
        self.clear_ai_output()
        if entry["ai"]:
            self.ai_markdown_sections = [entry["ai"]]
            self.ai_output.setMarkdown(entry["ai"])

    def reset_ai_context(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.clear_ai_output()
        self.statusBar().showMessage("AI conversation context reset.", 3000)

    # ---------------- Execution Controls ----------------
    def _set_running_state(self, running: bool):
        self.btn_run_ai.setEnabled(not running)
        self.btn_run_direct.setEnabled(not running)
        self.btn_analyze_raw.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def _ensure_server_ready(self) -> bool:
        if get_kali_server_health(timeout=1.5).get("ok"):
            return True
        ans = QMessageBox.question(
            self,
            "Kali Server Offline",
            "Hindi pa tumatakbo ang kali-server-mcp sa 127.0.0.1:5000.\nGusto mo bang i-start ito ngayon?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            proc = subprocess.run([MANAGER_SCRIPT, "start"], capture_output=True, text=True, timeout=15)
            self.refresh_server_status()
            if proc.stdout:
                self.append_raw_log(proc.stdout.strip(), level="info")
            return get_kali_server_health(timeout=2.0).get("ok")
        return False

    def run_ai_scan(self):
        if self.current_worker and self.current_worker.isRunning():
            return

        target = self.target_input.text().strip()
        prompt_text = self.prompt_input.toPlainText().strip()
        if not target and not prompt_text:
            QMessageBox.warning(self, "Missing Input", "Ilagay muna ang Target o ang AI Prompt sa kaliwa.")
            return

        provider = self.provider_combo.currentData()
        model = self.model_input.text().strip()
        cfg = resolve_provider_config(provider=provider, model=model or None)
        if not cfg["api_key"] and not cfg["base_url"]:
            QMessageBox.critical(
                self,
                "Missing API Key",
                f"Walang API key para sa {cfg['provider_label']}. I-launch gamit ang ./run-gui.sh o i-export ang NVIDIA_API_KEY / OPENAI_API_KEY.",
            )
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

        self.messages.append({"role": "user", "content": full_prompt})
        self._set_running_state(True)
        self.statusBar().showMessage(f"Running AI ({cfg['provider_label']}: {cfg['model']})...")

        worker = AgentWorker(
            provider=cfg["provider"],
            model=cfg["model"],
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            messages=self.messages,
            auto_approve=self.auto_approve_chk.isChecked(),
        )
        worker.reasoning_received.connect(lambda r: self.append_raw_log(f"[AI Reasoning]\n{r}", level="info"))
        worker.assistant_received.connect(self.append_ai_section)
        worker.tool_planned.connect(self._on_tool_planned)
        worker.approval_requested.connect(self._on_approval_requested)
        worker.tool_executing.connect(lambda name, _args: self.append_raw_log(f"[*] Executing {name}...", level="info"))
        worker.tool_result_received.connect(self._on_tool_result)
        worker.error_received.connect(lambda etype, msg: self.append_raw_log(f"[!] {etype.upper()} Error: {msg}", level="error"))
        worker.finished_turn.connect(lambda updated_msgs: self._on_ai_finished(updated_msgs, target or "Prompt"))
        self.current_worker = worker
        worker.start()

    def run_direct_tool(self):
        if self.current_worker and self.current_worker.isRunning():
            return

        tool_key = self.direct_tool_combo.currentData()
        target = self.target_input.text().strip()
        prompt_text = self.prompt_input.toPlainText().strip()

        if tool_key == "execute_command":
            if not prompt_text:
                QMessageBox.warning(self, "Missing Command", "Ilagay ang shell command sa Prompt box.")
                return
            tool_name = "execute_command"
            tool_args = {"command": prompt_text}
        elif tool_key == "tls_dns":
            if not target:
                QMessageBox.warning(self, "Missing Target", "Ilagay muna ang Target domain/IP.")
                return
            host = target.replace("https://", "").replace("http://", "").split("/")[0]
            qhost = shlex.quote(host)
            cmd = (
                f"echo | openssl s_client -connect {qhost}:443 -servername {qhost} 2>&1 | head -n 65; "
                f"echo '--- DNS ---'; dig +short {qhost} A {qhost} NS {qhost} TXT"
            )
            tool_name = "execute_command"
            tool_args = {"command": cmd}
        else:
            if not target:
                QMessageBox.warning(self, "Missing Target", "Ilagay muna ang Target IP, domain, o URL.")
                return
            tool_name = tool_key
            if tool_key == "nmap_scan":
                tool_args = {"target": target, "scan_type": "-sCV", "additional_args": "-T4"}
            elif tool_key == "nikto_scan":
                tool_args = {"target": target}
            elif tool_key == "gobuster_scan":
                url = target if target.startswith(("http://", "https://")) else f"http://{target}"
                tool_args = {"url": url, "mode": "dir", "wordlist": "/usr/share/wordlists/dirb/common.txt"}
            elif tool_key == "sqlmap_scan":
                url = target if target.startswith(("http://", "https://")) else f"http://{target}"
                tool_args = {"url": url, "additional_args": "--batch"}
            else:
                tool_args = {"target": target}

        if not self._ensure_server_ready():
            return

        ts = datetime.now().strftime("%H:%M:%S")
        self.append_raw_log(f"\n=== [{ts}] Direct: {tool_name} | {json.dumps(tool_args)} ===", level="cmd")
        self._set_running_state(True)
        self.statusBar().showMessage(f"Executing {tool_name} directly on Kali server...")

        worker = DirectToolWorker(tool_name, tool_args)
        worker.tool_result_received.connect(self._on_tool_result)
        worker.finished_direct.connect(lambda: self._on_direct_finished(tool_name, target or "Command"))
        self.current_worker = worker
        worker.start()

    def analyze_current_raw_output(self):
        raw_text = self.raw_output.toPlainText().strip()
        if not raw_text:
            QMessageBox.information(self, "No Output", "Wala pang raw output na ia-analyze.")
            return
        target = self.target_input.text().strip() or "current target"
        snippet = raw_text[-12000:]
        self.prompt_input.setPlainText(
            f"Analyze this scan output for {target}. Highlight open services, security issues, and next steps:\n\n{snippet}"
        )
        self.run_ai_scan()

    def stop_current_run(self):
        if isinstance(self.current_worker, AgentWorker):
            self.current_worker.request_stop()
        self.approval_bar.hide()
        self.append_raw_log("[!] Stop requested by user.", level="error")
        self.statusBar().showMessage("Stopping...")

    def _on_tool_planned(self, fn_name: str, _fn_args: Dict[str, Any], cmd_preview: str):
        self.append_raw_log(f"\n[ACTION] {fn_name}: {cmd_preview}", level="cmd")

    def _on_approval_requested(self, fn_name: str, _fn_args: Dict[str, Any], cmd_preview: str):
        self.approval_label.setText(f"Approve tool '{fn_name}'?\n{cmd_preview}")
        self.approval_bar.show()
        self.statusBar().showMessage(f"Waiting for approval: {fn_name}")

    def _respond_approval(self, approved: bool):
        self.approval_bar.hide()
        if isinstance(self.current_worker, AgentWorker):
            self.current_worker.provide_approval(approved)
        self.append_raw_log("[✓] Approved." if approved else "[✗] Declined by user.", level="success" if approved else "error")

    def _on_tool_result(self, fn_name: str, raw_result: Dict[str, Any]):
        stdout = (raw_result.get("stdout") or "").strip()
        stderr = (raw_result.get("stderr") or "").strip()
        err = raw_result.get("error")

        if stdout:
            self.append_raw_log(stdout, level="stdout")
        if stderr:
            self.append_raw_log(f"[stderr]\n{stderr}", level="stderr")
        if err and not stderr:
            self.append_raw_log(f"[error] {err}", level="error")
        if not stdout and not stderr and not err:
            self.append_raw_log(f"[{fn_name}] Completed with empty output: {json.dumps(raw_result)}", level="info")

    def _on_ai_finished(self, updated_messages: List[Dict[str, Any]], label_target: str):
        self.messages = updated_messages
        self.approval_bar.hide()
        self._set_running_state(False)
        self._save_history_snapshot("AI Scan", label_target)
        self.statusBar().showMessage("AI task finished.", 4000)

    def _on_direct_finished(self, tool_name: str, label_target: str):
        self._set_running_state(False)
        self._save_history_snapshot(tool_name, label_target)
        self.statusBar().showMessage(f"Direct {tool_name} finished.", 4000)

    def closeEvent(self, event):
        if isinstance(self.current_worker, AgentWorker) and self.current_worker.isRunning():
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
