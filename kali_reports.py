#!/usr/bin/env python3
"""
Kali MCP Report & Writeup Generator
-----------------------------------
Generates self-contained Markdown (.md) and dark/print-friendly HTML (.html)
lab/CTF engagement reports from SQLite workspace data.
"""

import html
from datetime import datetime
from typing import Any, Dict, List


def _severity_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
    for f in findings:
        sev = f.get("severity", "Info")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def generate_markdown_report(
    engagement: Dict[str, Any],
    findings: List[Dict[str, Any]],
    scans: List[Dict[str, Any]],
    ai_summary: str = "",
) -> str:
    """Build a clean Markdown report for a lab or CTF engagement."""
    counts = _severity_counts(findings)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = [
        f"# Kali MCP Engagement Report — {engagement.get('name', 'Lab / CTF')}",
        "",
        f"- **Generated:** {generated_at}",
        f"- **Primary Target:** `{engagement.get('target') or 'N/A'}`",
        f"- **Total Scans:** {len(scans)}",
        f"- **Total Findings:** {len(findings)} "
        f"(Critical: {counts['Critical']}, High: {counts['High']}, Medium: {counts['Medium']}, Low: {counts['Low']}, Info: {counts['Info']})",
        "",
    ]

    notes = (engagement.get("notes") or "").strip()
    if notes:
        lines.extend(["## Lab / CTF Notes & Artifacts", "", notes, ""])

    if ai_summary.strip():
        lines.extend(["## AI Analysis & Attack Path Summary", "", ai_summary.strip(), ""])

    lines.extend(["## Findings & Discovered Assets", ""])
    if findings:
        lines.extend(
            [
                "| Severity | Host | Port | Service | Finding | Source |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ]
        )
        for f in findings:
            title = str(f.get("title", "")).replace("|", "\\|")
            lines.append(
                f"| **{f.get('severity', 'Info')}** | `{f.get('host', '-')}` | `{f.get('port', '-')}` | "
                f"`{f.get('service', '-')}` | {title} | `{f.get('source_tool', '-')}` |"
            )
        lines.append("")
    else:
        lines.extend(["_No structured findings recorded yet._", ""])

    lines.extend(["## Raw Scan Evidence", ""])
    for s in scans[:10]:
        lines.extend(
            [
                f"### {s.get('title', 'Scan')} ({s.get('created_at', '')})",
                "",
                "```text",
                (s.get("raw_output") or "").strip()[:8000],
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def generate_html_report(
    engagement: Dict[str, Any],
    findings: List[Dict[str, Any]],
    scans: List[Dict[str, Any]],
    ai_summary: str = "",
) -> str:
    """Build a standalone styled HTML report ready for browser viewing or PDF printing."""
    counts = _severity_counts(findings)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sev_colors = {
        "Critical": "#f85149",
        "High": "#db6d28",
        "Medium": "#d29922",
        "Low": "#58a6ff",
        "Info": "#8b949e",
    }

    finding_rows = []
    for f in findings:
        sev = f.get("severity", "Info")
        color = sev_colors.get(sev, "#8b949e")
        finding_rows.append(
            f"<tr>"
            f"<td><span class='badge' style='border-color:{color};color:{color};'>{html.escape(sev)}</span></td>"
            f"<td><code>{html.escape(str(f.get('host', '-')))}</code></td>"
            f"<td><code>{html.escape(str(f.get('port', '-')))}</code></td>"
            f"<td><code>{html.escape(str(f.get('service', '-')))}</code></td>"
            f"<td><strong>{html.escape(str(f.get('title', '')))}</strong><div class='sub'>{html.escape(str(f.get('details', '')))}</div></td>"
            f"<td><code>{html.escape(str(f.get('source_tool', '-')))}</code></td>"
            f"</tr>"
        )

    scan_blocks = []
    for s in scans[:10]:
        scan_blocks.append(
            f"<details open><summary>{html.escape(str(s.get('title', 'Scan')))} — {html.escape(str(s.get('created_at', '')))}</summary>"
            f"<pre>{html.escape((s.get('raw_output') or '').strip()[:8000])}</pre></details>"
        )

    notes_html = (
        f"<section><h2>Lab / CTF Notes &amp; Flags</h2><pre>{html.escape((engagement.get('notes') or '').strip())}</pre></section>"
        if (engagement.get("notes") or "").strip()
        else ""
    )
    ai_html = (
        f"<section><h2>AI Analysis &amp; Findings</h2><pre class='wrap'>{html.escape(ai_summary.strip())}</pre></section>"
        if ai_summary.strip()
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Kali MCP Report — {html.escape(str(engagement.get('name', 'Lab / CTF')))}</title>
<style>
  body {{ background:#0d1117; color:#e6edf3; font-family:Inter,Segoe UI,sans-serif; margin:32px auto; max-width:1100px; padding:0 20px; }}
  h1, h2 {{ color:#58a6ff; }}
  .meta {{ display:flex; gap:18px; flex-wrap:wrap; background:#161b22; border:1px solid #30363d; border-radius:8px; padding:14px 18px; margin-bottom:20px; }}
  .stat {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:10px 16px; min-width:100px; text-align:center; }}
  .stats {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; }}
  table {{ width:100%; border-collapse:collapse; background:#161b22; border:1px solid #30363d; border-radius:8px; overflow:hidden; }}
  th, td {{ padding:10px 12px; border-bottom:1px solid #21262d; text-align:left; vertical-align:top; font-size:13px; }}
  th {{ background:#090c10; color:#58a6ff; text-transform:uppercase; font-size:11px; }}
  .badge {{ border:1px solid; border-radius:999px; padding:2px 8px; font-size:11px; font-weight:700; }}
  .sub {{ color:#8b949e; font-size:12px; margin-top:4px; }}
  pre {{ background:#090c10; border:1px solid #30363d; border-radius:6px; padding:12px; overflow-x:auto; font-family:'JetBrains Mono',monospace; font-size:12px; }}
  pre.wrap {{ white-space:pre-wrap; font-family:Inter,Segoe UI,sans-serif; font-size:13px; }}
  details {{ margin-bottom:12px; }}
  summary {{ cursor:pointer; font-weight:600; color:#e6edf3; padding:6px 0; }}
</style>
</head>
<body>
  <h1>Kali MCP Engagement Report — {html.escape(str(engagement.get('name', 'Lab / CTF')))}</h1>
  <div class="meta">
    <div><strong>Target:</strong> <code>{html.escape(str(engagement.get('target') or 'N/A'))}</code></div>
    <div><strong>Generated:</strong> {html.escape(generated_at)}</div>
    <div><strong>Scans:</strong> {len(scans)}</div>
  </div>
  <div class="stats">
    <div class="stat"><div style="color:#f85149;font-size:20px;font-weight:800;">{counts['Critical']}</div><div>Critical</div></div>
    <div class="stat"><div style="color:#db6d28;font-size:20px;font-weight:800;">{counts['High']}</div><div>High</div></div>
    <div class="stat"><div style="color:#d29922;font-size:20px;font-weight:800;">{counts['Medium']}</div><div>Medium</div></div>
    <div class="stat"><div style="color:#58a6ff;font-size:20px;font-weight:800;">{counts['Low']}</div><div>Low</div></div>
    <div class="stat"><div style="color:#8b949e;font-size:20px;font-weight:800;">{counts['Info']}</div><div>Info</div></div>
  </div>
  {notes_html}
  {ai_html}
  <section>
    <h2>Findings &amp; Discovered Assets</h2>
    <table>
      <thead><tr><th>Severity</th><th>Host</th><th>Port</th><th>Service</th><th>Finding</th><th>Source</th></tr></thead>
      <tbody>{"".join(finding_rows) or "<tr><td colspan='6'>No findings recorded.</td></tr>"}</tbody>
    </table>
  </section>
  <section>
    <h2>Raw Scan Evidence</h2>
    {"".join(scan_blocks) or "<p>No scan logs recorded.</p>"}
  </section>
</body>
</html>"""
