#!/usr/bin/env python3
"""
Kali MCP Output Parsers
-----------------------
Extracts structured findings (ports, services, web paths, vulnerabilities, TLS/DNS,
and searchsploit matches) from raw tool outputs for the GUI Findings & Assets table.
"""

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class Finding:
    severity: str  # Critical, High, Medium, Low, Info
    host: str
    port: str
    service: str
    title: str
    details: str
    source_tool: str
    follow_up_tool: str = ""
    follow_up_target: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _norm_host(target: str) -> str:
    cleaned = target.strip()
    cleaned = re.sub(r"^https?://", "", cleaned)
    return cleaned.split("/")[0].split(":")[0] or target


def parse_nmap_output(text: str, target: str) -> List[Finding]:
    """Parse Nmap port lines and script outputs into structured Findings."""
    findings: List[Finding] = []
    host = _norm_host(target)
    port_re = re.compile(r"^(\d+/(?:tcp|udp))\s+(open|filtered|open\|filtered)\s+(\S+)(?:\s+(.*))?$", re.IGNORECASE)

    risky_ports = {
        "21": ("Medium", "FTP service exposed"),
        "22": ("Info", "SSH service exposed"),
        "23": ("High", "Telnet plaintext service exposed"),
        "80": ("Info", "HTTP web service exposed"),
        "139": ("Medium", "NetBIOS / SMB port exposed"),
        "443": ("Info", "HTTPS web service exposed"),
        "445": ("Medium", "SMB file sharing exposed"),
        "3306": ("Medium", "MySQL database port exposed"),
        "3389": ("Medium", "RDP remote desktop exposed"),
        "5432": ("Medium", "PostgreSQL database port exposed"),
        "6379": ("High", "Redis port exposed"),
        "27017": ("High", "MongoDB port exposed"),
    }

    for line in text.splitlines():
        m = port_re.match(line.strip())
        if not m:
            continue
        port_proto, state, service, version = m.groups()
        port_num = port_proto.split("/")[0]
        version_str = (version or "").strip()

        sev, base_title = risky_ports.get(port_num, ("Info", f"Open port {port_proto} ({service})"))
        if state.lower() != "open":
            sev = "Info"

        follow_tool = ""
        follow_target = target
        svc_lower = service.lower()
        if "http" in svc_lower or port_num in ("80", "443", "8080", "8443"):
            scheme = "https" if ("ssl" in svc_lower or "https" in svc_lower or port_num in ("443", "8443")) else "http"
            follow_tool = "nikto_scan"
            follow_target = f"{scheme}://{host}:{port_num}" if port_num not in ("80", "443") else f"{scheme}://{host}"
        elif port_num in ("139", "445") or "smb" in svc_lower or "netbios" in svc_lower:
            follow_tool = "enum4linux_scan"
            follow_target = host
        elif version_str:
            follow_tool = "searchsploit"
            follow_target = " ".join(version_str.split()[:3])

        findings.append(
            Finding(
                severity=sev,
                host=host,
                port=port_proto,
                service=service,
                title=f"{base_title}" + (f" — {version_str}" if version_str else ""),
                details=f"State: {state}" + (f" | Banner/Version: {version_str}" if version_str else ""),
                source_tool="nmap_scan",
                follow_up_tool=follow_tool,
                follow_up_target=follow_target,
            )
        )

    return findings


def parse_gobuster_output(text: str, target: str) -> List[Finding]:
    """Parse Gobuster / Dirb discovered paths and status codes."""
    findings: List[Finding] = []
    host = _norm_host(target)
    sensitive_keywords = (
        "admin",
        "login",
        "backup",
        ".git",
        ".env",
        "config",
        "sql",
        "phpinfo",
        "upload",
        "secret",
        "flag",
        "api",
        "dashboard",
    )

    gobuster_re = re.compile(r"^(/\S+)\s+\(Status:\s*(\d+)\)(?:\s*\[Size:\s*(\d+)\])?", re.IGNORECASE)
    dirb_re = re.compile(r"^\+\s+(https?://\S+)\s+\(CODE:(\d+)\|SIZE:(\d+)\)", re.IGNORECASE)

    for raw in text.splitlines():
        line = raw.strip()
        m_go = gobuster_re.match(line)
        m_dirb = dirb_re.match(line)
        if m_go:
            path, status, size = m_go.groups()
            is_sensitive = any(k in path.lower() for k in sensitive_keywords)
            sev = "Medium" if (is_sensitive and status in ("200", "301", "302", "401", "403")) else "Info"
            findings.append(
                Finding(
                    severity=sev,
                    host=host,
                    port="web",
                    service="http",
                    title=f"Discovered path {path} (HTTP {status})",
                    details=f"Status: {status}" + (f" | Size: {size} bytes" if size else ""),
                    source_tool="gobuster_scan",
                    follow_up_tool="nikto_scan",
                    follow_up_target=target,
                )
            )
        elif m_dirb:
            url, status, size = m_dirb.groups()
            is_sensitive = any(k in url.lower() for k in sensitive_keywords)
            sev = "Medium" if (is_sensitive and status in ("200", "301", "302", "401", "403")) else "Info"
            findings.append(
                Finding(
                    severity=sev,
                    host=host,
                    port="web",
                    service="http",
                    title=f"Discovered URL {url} (HTTP {status})",
                    details=f"Status: {status} | Size: {size} bytes",
                    source_tool="dirb_scan",
                )
            )

    return findings


def parse_nikto_output(text: str, target: str) -> List[Finding]:
    """Parse Nikto '+' finding lines."""
    findings: List[Finding] = []
    host = _norm_host(target)
    high_kw = ("sql injection", "remote code", "rce", "arbitrary file", "shell", "traversal")
    med_kw = ("xss", "csrf", "directory indexing", "outdated", "vulnerable", "default account", "phpinfo", ".git", "backup")
    skip_prefixes = ("Target IP:", "Target Hostname:", "Target Port:", "Start Time:", "End Time:", "Server:")

    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("+ "):
            continue
        body = line[2:].strip()
        if not body or body.startswith(skip_prefixes):
            continue
        low = body.lower()
        if any(k in low for k in high_kw):
            sev = "High"
        elif any(k in low for k in med_kw):
            sev = "Medium"
        elif "missing" in low or "header" in low:
            sev = "Low"
        else:
            sev = "Info"

        findings.append(
            Finding(
                severity=sev,
                host=host,
                port="web",
                service="http",
                title=body[:120] + ("..." if len(body) > 120 else ""),
                details=body,
                source_tool="nikto_scan",
            )
        )
    return findings


def parse_sqlmap_output(text: str, target: str) -> List[Finding]:
    """Parse SQLmap injectable parameter / database findings."""
    findings: List[Finding] = []
    host = _norm_host(target)

    for m in re.finditer(r"Parameter:\s*(.+?)\s+is vulnerable", text, re.IGNORECASE):
        param = m.group(1).strip()
        findings.append(
            Finding(
                severity="Critical",
                host=host,
                port="web",
                service="http",
                title=f"SQL Injection confirmed on parameter '{param}'",
                details="SQLmap reported an injectable parameter.",
                source_tool="sqlmap_scan",
            )
        )

    db_match = re.search(r"available databases\s*\[\d+\]:\s*\n((?:\[\*\]\s*.+\n?)+)", text, re.IGNORECASE)
    if db_match:
        dbs = [d.strip(" [*]-\t") for d in db_match.group(1).splitlines() if d.strip()]
        if dbs:
            findings.append(
                Finding(
                    severity="Critical",
                    host=host,
                    port="web",
                    service="http",
                    title=f"Enumerated SQL databases ({len(dbs)})",
                    details=", ".join(dbs[:15]),
                    source_tool="sqlmap_scan",
                )
            )
    return findings


def parse_tls_dns_output(text: str, target: str) -> List[Finding]:
    """Parse OpenSSL TLS and DNS dig inspection output."""
    findings: List[Finding] = []
    host = _norm_host(target)

    proto_m = re.search(r"Protocol\s*:\s*(TLSv[\d.]+|SSLv[\d.]+)", text)
    if proto_m:
        proto = proto_m.group(1)
        sev = "Medium" if proto in ("SSLv2", "SSLv3", "TLSv1", "TLSv1.0", "TLSv1.1") else "Info"
        findings.append(
            Finding(
                severity=sev,
                host=host,
                port="443/tcp",
                service="tls",
                title=f"Negotiated {proto}",
                details=f"TLS protocol observed: {proto}",
                source_tool="tls_dns",
            )
        )

    verify_m = re.search(r"Verify return code:\s*(.+)", text)
    if verify_m:
        code_str = verify_m.group(1).strip()
        sev = "Info" if code_str.startswith("0 (ok)") else "Medium"
        findings.append(
            Finding(
                severity=sev,
                host=host,
                port="443/tcp",
                service="tls",
                title=f"Certificate verification: {code_str}",
                details=code_str,
                source_tool="tls_dns",
            )
        )

    return findings


def parse_searchsploit_json(text: str, query: str) -> List[Finding]:
    """Parse `searchsploit --json` output into exploit Findings."""
    findings: List[Finding] = []
    start = text.find("{")
    if start == -1:
        return findings
    try:
        data = json.loads(text[start:])
    except Exception:
        return findings

    for item in data.get("RESULTS_EXPLOIT", [])[:20]:
        title = item.get("Title", "Exploit Match")
        edb_id = item.get("EDB-ID", "")
        path = item.get("Path", "")
        findings.append(
            Finding(
                severity="High",
                host=query,
                port="-",
                service="exploit-db",
                title=f"[EDB-{edb_id}] {title}" if edb_id else title,
                details=f"Path: {path}",
                source_tool="searchsploit",
            )
        )
    return findings


def parse_tool_output(tool_name: str, text: str, target: str) -> List[Finding]:
    """Dispatch raw tool output to the matching parser(s)."""
    if not text or not text.strip():
        return []

    findings: List[Finding] = []
    if tool_name == "nmap_scan":
        findings.extend(parse_nmap_output(text, target))
    elif tool_name in ("gobuster_scan", "dirb_scan"):
        findings.extend(parse_gobuster_output(text, target))
    elif tool_name == "nikto_scan":
        findings.extend(parse_nikto_output(text, target))
    elif tool_name == "sqlmap_scan":
        findings.extend(parse_sqlmap_output(text, target))
    elif tool_name in ("tls_dns", "tls_http_check"):
        findings.extend(parse_tls_dns_output(text, target))
    elif tool_name == "searchsploit":
        findings.extend(parse_searchsploit_json(text, target))
    elif tool_name == "execute_command":
        if "RESULTS_EXPLOIT" in text:
            findings.extend(parse_searchsploit_json(text, target))
        if "Nmap scan report" in text or re.search(r"^\d+/(?:tcp|udp)\s+open\s+", text, re.MULTILINE):
            findings.extend(parse_nmap_output(text, target))
        if "Verify return code:" in text or "Protocol  :" in text:
            findings.extend(parse_tls_dns_output(text, target))
    return findings
