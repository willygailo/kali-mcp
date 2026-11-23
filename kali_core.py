#!/usr/bin/env python3
"""
Kali MCP Shared Core
--------------------
Shared LLM provider configuration, Kali MCP API client helpers, tool definitions,
and callback-driven agent loop used by both kali-agent.py (CLI) and kali-gui.py (GUI).
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, cast

import requests
from openai import OpenAI


def _load_dotenv() -> None:
    """Load key=value pairs from local .env without overwriting existing env vars."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, val)
    except OSError:
        pass


_load_dotenv()

DEFAULT_KALI_SERVER_URL = os.environ.get("KALI_SERVER_URL", "http://127.0.0.1:5000").rstrip("/")

# Disable proxy for localhost communication
http_session = requests.Session()
http_session.trust_env = False

SYSTEM_PROMPT = """You are an offensive security AI assistant running directly in a Kali Linux environment.
You have direct access to execute Kali tools and terminal commands through the Kali MCP server.

Available tools include:
- execute_command: Execute any terminal command (bash, bash utilities, scripts).
- nmap_scan: Run network port and service scanning.
- gobuster_scan: Brute force directories, files, DNS subdomains, or vhosts.
- dirb_scan: Web content scanner.
- nikto_scan: Web server vulnerability scanner.
- sqlmap_scan: Automated SQL injection scanner.
- metasploit_run: Run Metasploit modules.
- hydra_attack: Password brute-forcing.
- john_crack: Hash cracking.
- wpscan_analyze: WordPress vulnerability scanner.
- enum4linux_scan: Windows/Samba enumeration.

Guidelines:
1. Always analyze target results and provide clear, actionable summaries.
2. When executing tools, suggest appropriate flags (e.g. -T4, -sC, -sV for nmap).
3. If an error occurs, analyze stdout/stderr and suggest alternatives or fixes.
4. Always operate within legal and authorized boundaries (ethical hacking / authorized pentesting / CTFs).
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute an arbitrary shell command on the Kali Linux machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The exact shell command to run (e.g., 'uname -a', 'which nmap', 'curl -I http://example.com')",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nmap_scan",
            "description": "Execute an Nmap port or vulnerability scan against a target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target IP or hostname"},
                    "scan_type": {"type": "string", "description": "Scan type (e.g., '-sCV', '-sS', '-sU')", "default": "-sCV"},
                    "ports": {"type": "string", "description": "Comma-separated ports or range (e.g., '80,443' or '1-1000')", "default": ""},
                    "additional_args": {"type": "string", "description": "Additional Nmap arguments (e.g., '-T4 -Pn')", "default": "-T4"},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gobuster_scan",
            "description": "Execute Gobuster directory/file or DNS enumeration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "mode": {"type": "string", "enum": ["dir", "dns", "fuzz", "vhost"], "default": "dir"},
                    "wordlist": {"type": "string", "description": "Wordlist path", "default": "/usr/share/wordlists/dirb/common.txt"},
                    "additional_args": {"type": "string", "description": "Additional flags", "default": ""},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nikto_scan",
            "description": "Execute Nikto web server scanner against a target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target URL or IP"},
                    "additional_args": {"type": "string", "description": "Additional Nikto arguments", "default": ""},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sqlmap_scan",
            "description": "Execute SQLmap against a target URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "data": {"type": "string", "description": "POST data string", "default": ""},
                    "additional_args": {"type": "string", "description": "Additional SQLmap arguments (e.g., '--batch --dbs')", "default": "--batch"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "john_crack",
            "description": "Execute John the Ripper to crack password hashes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hash_file": {"type": "string", "description": "File containing password hashes"},
                    "wordlist": {"type": "string", "description": "Wordlist path", "default": "/usr/share/wordlists/rockyou.txt"},
                    "format_type": {"type": "string", "description": "Hash format (e.g., 'raw-md5', 'nt')", "default": ""},
                    "additional_args": {"type": "string", "description": "Additional arguments", "default": ""},
                },
                "required": ["hash_file"],
            },
        },
    },
]


@dataclass
class AgentCallbacks:
    """Optional hooks emitted during an AI agent chat turn."""

    on_reasoning: Optional[Callable[[str], None]] = None
    on_assistant_message: Optional[Callable[[str], None]] = None
    on_tool_planned: Optional[Callable[[str, Dict[str, Any], str], None]] = None
    on_confirm: Optional[Callable[[str, Dict[str, Any], str], bool]] = None
    on_tool_executing: Optional[Callable[[str, Dict[str, Any]], None]] = None
    on_tool_result: Optional[Callable[[str, Dict[str, Any]], None]] = None
    on_error: Optional[Callable[[str, str], None]] = None
    should_stop: Optional[Callable[[], bool]] = None


def resolve_provider_config(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve provider ('nvidia' or 'openai'), model, API key, and base URL."""
    nvidia_key = os.environ.get("NVIDIA_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    chosen_provider = provider
    if not chosen_provider:
        if api_key and api_key.startswith("nvapi-"):
            chosen_provider = "nvidia"
        elif api_key and api_key.startswith("sk-"):
            chosen_provider = "openai"
        elif nvidia_key:
            chosen_provider = "nvidia"
        else:
            chosen_provider = "openai"

    if chosen_provider == "nvidia":
        default_base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        default_model = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
        resolved_key = api_key or nvidia_key
        provider_label = "NVIDIA NIM"
    else:
        default_base_url = None
        default_model = "gpt-4o"
        resolved_key = api_key or openai_key
        provider_label = "OpenAI"

    resolved_base_url = base_url or os.environ.get("LLM_BASE_URL") or default_base_url
    resolved_model = model or os.environ.get("LLM_MODEL") or default_model

    return {
        "provider": chosen_provider,
        "provider_label": provider_label,
        "model": resolved_model,
        "api_key": resolved_key,
        "base_url": resolved_base_url,
    }


def create_openai_client(api_key: Optional[str], base_url: Optional[str] = None) -> OpenAI:
    """Create an OpenAI-compatible client for OpenAI or NVIDIA NIM."""
    resolved_key = api_key or "dummy-key"
    if base_url:
        return OpenAI(api_key=resolved_key, base_url=base_url)
    return OpenAI(api_key=resolved_key)


def get_kali_server_health(server_url: Optional[str] = None, timeout: float = 3.0) -> Dict[str, Any]:
    """Fetch health JSON from kali-server-mcp, returning {'ok': bool, ...}."""
    base = (server_url or DEFAULT_KALI_SERVER_URL).rstrip("/")
    try:
        r = http_session.get(f"{base}/health", timeout=timeout)
        if r.status_code == 200:
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return {"ok": True, "status_code": 200, "data": data}
        return {"ok": False, "status_code": r.status_code, "error": f"HTTP {r.status_code}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_kali_server(server_url: Optional[str] = None) -> bool:
    """Return True if kali-server-mcp is reachable and healthy."""
    return bool(get_kali_server_health(server_url=server_url).get("ok"))


def call_kali_api(
    tool_name: str,
    arguments: Dict[str, Any],
    server_url: Optional[str] = None,
    timeout: int = 300,
) -> Dict[str, Any]:
    """Execute a tool against the Kali MCP HTTP API server."""
    base = (server_url or DEFAULT_KALI_SERVER_URL).rstrip("/")
    endpoint_map = {
        "execute_command": ("api/command", lambda args: {"command": args.get("command", "")}),
        "nmap_scan": (
            "api/tools/nmap",
            lambda args: {
                "target": args.get("target"),
                "scan_type": args.get("scan_type", "-sCV"),
                "ports": args.get("ports", ""),
                "additional_args": args.get("additional_args", "-T4"),
            },
        ),
        "gobuster_scan": (
            "api/tools/gobuster",
            lambda args: {
                "url": args.get("url"),
                "mode": args.get("mode", "dir"),
                "wordlist": args.get("wordlist", "/usr/share/wordlists/dirb/common.txt"),
                "additional_args": args.get("additional_args", ""),
            },
        ),
        "nikto_scan": (
            "api/tools/nikto",
            lambda args: {
                "target": args.get("target"),
                "additional_args": args.get("additional_args", ""),
            },
        ),
        "sqlmap_scan": (
            "api/tools/sqlmap",
            lambda args: {
                "url": args.get("url"),
                "data": args.get("data", ""),
                "additional_args": args.get("additional_args", "--batch"),
            },
        ),
        "john_crack": (
            "api/tools/john",
            lambda args: {
                "hash_file": args.get("hash_file"),
                "wordlist": args.get("wordlist", "/usr/share/wordlists/rockyou.txt"),
                "format": args.get("format_type", ""),
                "additional_args": args.get("additional_args", ""),
            },
        ),
    }

    if tool_name not in endpoint_map:
        return {"error": f"Unknown tool: {tool_name}", "success": False}

    endpoint, payload_builder = endpoint_map[tool_name]
    payload = payload_builder(arguments)

    try:
        url = f"{base}/{endpoint}"
        response = http_session.post(url, json=payload, timeout=timeout)
        return response.json()
    except Exception as exc:
        return {"error": str(exc), "success": False}


def run_chat_turn(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, Any]],
    auto_approve: bool = False,
    callbacks: Optional[AgentCallbacks] = None,
    server_url: Optional[str] = None,
) -> None:
    """Execute a model completion turn and handle any tool calls via callbacks."""
    cb = callbacks or AgentCallbacks()

    while True:
        if cb.should_stop and cb.should_stop():
            return

        try:
            response = client.chat.completions.create(
                model=model,
                messages=cast(Any, messages),
                tools=cast(Any, TOOL_DEFINITIONS),
                tool_choice="auto",
                max_tokens=4096,
            )
        except Exception as exc:
            err_str = str(exc)
            if "insufficient_quota" in err_str or "credit_balance_exhausted" in err_str:
                if cb.on_error:
                    cb.on_error("quota", "Walang available credits ang API key mo.")
            elif "invalid_api_key" in err_str or "401" in err_str:
                if cb.on_error:
                    cb.on_error("auth", "Mali o expired ang API key mo.")
            else:
                if cb.on_error:
                    cb.on_error("api", err_str)
            return

        if cb.should_stop and cb.should_stop():
            return

        msg = response.choices[0].message

        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning and cb.on_reasoning:
            cb.on_reasoning(reasoning)

        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            if msg.content and cb.on_assistant_message:
                cb.on_assistant_message(msg.content)
            break

        for tool_call in msg.tool_calls:
            if cb.should_stop and cb.should_stop():
                return

            fn_obj = getattr(tool_call, "function", None)
            if fn_obj is None:
                continue

            fn_name = fn_obj.name
            try:
                fn_args = json.loads(fn_obj.arguments)
            except Exception:
                fn_args = {}

            cmd_preview = fn_args.get("command") or json.dumps(fn_args)
            if cb.on_tool_planned:
                cb.on_tool_planned(fn_name, fn_args, cmd_preview)

            if not auto_approve:
                confirmed = True
                if cb.on_confirm:
                    confirmed = cb.on_confirm(fn_name, fn_args, cmd_preview)

                if not confirmed:
                    tool_result = {"cancelled": True, "message": "User declined execution."}
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result),
                        }
                    )
                    continue

            if cb.on_tool_executing:
                cb.on_tool_executing(fn_name, fn_args)

            raw_result = call_kali_api(fn_name, fn_args, server_url=server_url)

            if cb.on_tool_result:
                cb.on_tool_result(fn_name, raw_result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(raw_result),
                }
            )
