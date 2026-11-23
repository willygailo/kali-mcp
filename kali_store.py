#!/usr/bin/env python3
"""
Kali MCP SQLite Persistence Store
---------------------------------
Stores engagements/projects, scan history, structured findings, CTF/lab notes,
and AI chat messages across restarts.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.environ.get(
    "KALI_MCP_DB_PATH",
    os.path.join(os.path.expanduser("~"), ".local", "share", "kali-mcp", "projects.db"),
)


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ProjectStore:
    """Lightweight SQLite store for Kali MCP engagements and scan artifacts."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._init_schema()
        self.create_or_get_engagement("Default Lab / CTF")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS engagements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    target TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    target TEXT NOT NULL,
                    raw_output TEXT NOT NULL DEFAULT '',
                    ai_analysis TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    scan_id INTEGER,
                    severity TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port TEXT NOT NULL,
                    service TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    source_tool TEXT NOT NULL,
                    follow_up_tool TEXT NOT NULL DEFAULT '',
                    follow_up_target TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
                    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chat_contexts (
                    engagement_id INTEGER PRIMARY KEY,
                    messages_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
                );
                """
            )

    def list_engagements(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, target, notes, created_at, updated_at FROM engagements ORDER BY id ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def create_or_get_engagement(self, name: str, target: str = "") -> Dict[str, Any]:
        clean = name.strip() or "Default Lab / CTF"
        now = _now_iso()
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM engagements WHERE name = ?", (clean,)).fetchone()
            if existing:
                return dict(existing)
            cur = conn.execute(
                "INSERT INTO engagements (name, target, notes, created_at, updated_at) VALUES (?, ?, '', ?, ?)",
                (clean, target, now, now),
            )
            row = conn.execute("SELECT * FROM engagements WHERE id = ?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def get_engagement(self, engagement_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM engagements WHERE id = ?", (engagement_id,)).fetchone()
            return dict(row) if row else None

    def update_engagement_target(self, engagement_id: int, target: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE engagements SET target = ?, updated_at = ? WHERE id = ?",
                (target, _now_iso(), engagement_id),
            )

    def update_engagement_notes(self, engagement_id: int, notes: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE engagements SET notes = ?, updated_at = ? WHERE id = ?",
                (notes, _now_iso(), engagement_id),
            )

    def delete_engagement(self, engagement_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM engagements WHERE id = ?", (engagement_id,))
        if not self.list_engagements():
            self.create_or_get_engagement("Default Lab / CTF")

    def save_scan_and_findings(
        self,
        engagement_id: int,
        title: str,
        tool_name: str,
        target: str,
        raw_output: str,
        ai_analysis: str,
        findings: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        now = _now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO scans (engagement_id, title, tool_name, target, raw_output, ai_analysis, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (engagement_id, title, tool_name, target, raw_output, ai_analysis, now),
            )
            scan_id = int(cur.lastrowid or 0)

            for f in findings or []:
                conn.execute(
                    """
                    INSERT INTO findings (
                        engagement_id, scan_id, severity, host, port, service,
                        title, details, source_tool, follow_up_tool, follow_up_target, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        engagement_id,
                        scan_id,
                        f.get("severity", "Info"),
                        f.get("host", target),
                        f.get("port", "-"),
                        f.get("service", "-"),
                        f.get("title", ""),
                        f.get("details", ""),
                        f.get("source_tool", tool_name),
                        f.get("follow_up_tool", ""),
                        f.get("follow_up_target", ""),
                        now,
                    ),
                )
            conn.execute("UPDATE engagements SET updated_at = ? WHERE id = ?", (now, engagement_id))
            return scan_id

    def list_scans(self, engagement_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, engagement_id, title, tool_name, target, raw_output, ai_analysis, created_at
                FROM scans
                WHERE engagement_id = ?
                ORDER BY id DESC
                """,
                (engagement_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_findings(self, engagement_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, engagement_id, scan_id, severity, host, port, service,
                       title, details, source_tool, follow_up_tool, follow_up_target, created_at
                FROM findings
                WHERE engagement_id = ?
                ORDER BY
                    CASE severity
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                        ELSE 5
                    END,
                    id DESC
                """,
                (engagement_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def clear_findings(self, engagement_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM findings WHERE engagement_id = ?", (engagement_id,))

    def save_chat_messages(self, engagement_id: int, messages: List[Dict[str, Any]]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_contexts (engagement_id, messages_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(engagement_id) DO UPDATE SET
                    messages_json = excluded.messages_json,
                    updated_at = excluded.updated_at
                """,
                (engagement_id, json.dumps(messages), _now_iso()),
            )

    def load_chat_messages(self, engagement_id: int) -> Optional[List[Dict[str, Any]]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT messages_json FROM chat_contexts WHERE engagement_id = ?",
                (engagement_id,),
            ).fetchone()
            if not row:
                return None
            try:
                return json.loads(row["messages_json"])
            except Exception:
                return None
