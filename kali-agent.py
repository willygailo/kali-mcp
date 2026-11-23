#!/usr/bin/env python3
"""
Kali AI Terminal Agent
-----------------------
An interactive terminal assistant powered by multiple LLM providers (NVIDIA NIM,
ChatGPT / OpenAI, Google Gemini, Anthropic Claude, xAI Grok, or Custom / Local)
that interfaces with Kali Linux's mcp-kali-server (kali-server-mcp).
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console as _RichConsole
    from rich.markdown import Markdown as _RichMarkdown
    from rich.panel import Panel as _RichPanel
    from rich.prompt import Confirm as _RichConfirm, Prompt as _RichPrompt

    console: Optional[Any] = _RichConsole()
    Markdown: Optional[Any] = _RichMarkdown
    Panel: Optional[Any] = _RichPanel
    Confirm: Optional[Any] = _RichConfirm
    Prompt: Optional[Any] = _RichPrompt
except ImportError:
    console = None
    Markdown = None
    Panel = None
    Confirm = None
    Prompt = None

from kali_core import (
    AgentCallbacks,
    DEFAULT_KALI_SERVER_URL,
    SYSTEM_PROMPT,
    check_kali_server,
    create_openai_client,
    resolve_provider_config,
    run_chat_turn as core_run_chat_turn,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def print_msg(text: str, style: str = "bold white"):
    if console is not None:
        console.print(text, style=style)
    else:
        print(text)


def print_md(markdown_text: str):
    if console is not None and Markdown is not None:
        console.print(Markdown(markdown_text))
    else:
        print(markdown_text)


def run_chat_turn(client, model: str, messages: List[Dict[str, Any]], auto_approve: bool = False):
    """Execute a model completion turn using terminal output and prompts."""
    streamed_any = False

    def on_reasoning(reasoning: str):
        if console is not None and Panel is not None:
            console.print(Panel(reasoning, title="[dim italic]Reasoning Process[/dim italic]", border_style="dim"))
        else:
            print(f"[Thinking] {reasoning[:300]}...")

    def on_assistant_delta(piece: str):
        nonlocal streamed_any
        streamed_any = True
        sys.stdout.write(piece)
        sys.stdout.flush()

    def on_assistant_message(content: str):
        nonlocal streamed_any
        if streamed_any:
            print()
            streamed_any = False
        else:
            print_md(content)

    def on_tool_planned(fn_name: str, _fn_args: Dict[str, Any], cmd_preview: str):
        nonlocal streamed_any
        if streamed_any:
            print()
            streamed_any = False
        if console is not None and Panel is not None:
            console.print(
                Panel(
                    f"[bold cyan]Tool:[/bold cyan] {fn_name}\n[bold yellow]Args:[/bold yellow] {cmd_preview}",
                    title="[bold red]Kali MCP Action[/bold red]",
                    border_style="red",
                )
            )
        else:
            print(f"\n[ACTION] {fn_name}: {cmd_preview}")

    def on_confirm(_fn_name: str, _fn_args: Dict[str, Any], _cmd_preview: str) -> bool:
        if Confirm is not None:
            return Confirm.ask("Execute this tool call?", default=True)
        ans = input("Execute this tool call? [Y/n]: ").strip().lower()
        return ans in ("", "y", "yes")

    def on_tool_executing(_fn_name: str, _fn_args: Dict[str, Any]):
        print_msg("[*] Executing on Kali API server...", style="dim")

    def on_tool_result(_fn_name: str, raw_result: Dict[str, Any]):
        stdout = raw_result.get("stdout", "").strip()
        stderr = raw_result.get("stderr", "").strip()

        if stdout:
            if console is not None and Panel is not None:
                console.print(
                    Panel(
                        stdout[:2000] + ("\n...[truncated]" if len(stdout) > 2000 else ""),
                        title="[green]Output[/green]",
                        border_style="green",
                    )
                )
            else:
                print("--- OUTPUT ---")
                print(stdout[:2000])

        if stderr and raw_result.get("return_code", 0) != 0:
            print_msg(f"[-] Stderr: {stderr[:500]}", style="bold red")

    def on_error(err_type: str, message: str):
        if err_type == "quota":
            print_msg(f"\n[!] Quota Error: {message}", style="bold red")
            print_msg(
                "    Para sa OpenAI, mag-add ng credits sa https://platform.openai.com/settings/organization/billing/",
                style="yellow",
            )
        elif err_type == "auth":
            print_msg(f"\n[!] Auth Error: {message}", style="bold red")
        else:
            print_msg(f"\n[!] API Error: {message}", style="bold red")

    callbacks = AgentCallbacks(
        on_reasoning=on_reasoning,
        on_assistant_delta=on_assistant_delta,
        on_assistant_message=on_assistant_message,
        on_tool_planned=on_tool_planned,
        on_confirm=on_confirm,
        on_tool_executing=on_tool_executing,
        on_tool_result=on_tool_result,
        on_error=on_error,
    )
    core_run_chat_turn(client, model, messages, auto_approve=auto_approve, callbacks=callbacks)


def main():
    parser = argparse.ArgumentParser(description="Kali AI Terminal Agent")
    parser.add_argument("prompt", nargs="*", help="Initial prompt (optional)")
    parser.add_argument(
        "--provider",
        choices=["nvidia", "openai", "gemini", "claude", "grok", "custom"],
        default=None,
        help="LLM provider: nvidia, openai, gemini, claude, grok, or custom (auto-detected if omitted)",
    )
    parser.add_argument("--model", default=None, help="Model ID")
    parser.add_argument("--api-key", default=None, help="API Key")
    parser.add_argument("--base-url", default=None, help="Custom LLM API Base URL")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-approve all tool calls without prompting")
    args = parser.parse_args()

    cfg = resolve_provider_config(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )

    if not cfg["api_key"] and cfg["provider"] != "custom":
        env_key = cfg["env_key"]
        print(f"[-] Error: API key is not set for provider '{cfg['provider']}' ({cfg['provider_label']}).")
        print(f"    Please pass --api-key, add {env_key} to .env, or export {env_key}.")
        sys.exit(1)

    if not check_kali_server():
        print(f"[-] kali-server-mcp is not running on {DEFAULT_KALI_SERVER_URL}!")
        print("    Starting it with kali-mcp-manager.sh start...")
        os.system(os.path.join(SCRIPT_DIR, "kali-mcp-manager.sh") + " start")
        if not check_kali_server():
            print("[-] Failed to start Kali API Server. Check /tmp/kali-server-mcp.log")
            sys.exit(1)

    client = create_openai_client(cfg["api_key"], cfg["base_url"])

    if console is not None and Panel is not None:
        console.print(
            Panel.fit(
                f"[bold green]Kali MCP AI Terminal Assistant[/bold green]\n"
                f"[cyan]Provider:[/cyan] {cfg['provider_label']} | [cyan]Model:[/cyan] {cfg['model']}\n"
                f"[cyan]Backend:[/cyan] {DEFAULT_KALI_SERVER_URL}\n"
                f"Type [yellow]exit[/yellow] or [yellow]quit[/yellow] to end session.",
                border_style="green",
            )
        )
    else:
        print(f"=== Kali MCP AI Assistant ({cfg['provider_label']}: {cfg['model']}) ===")

    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if args.prompt:
        user_prompt = " ".join(args.prompt)
        print_msg(f"\nUser: {user_prompt}", style="bold cyan")
        messages.append({"role": "user", "content": user_prompt})
        run_chat_turn(client, cfg["model"], messages, auto_approve=args.yes)
        return

    while True:
        try:
            if Prompt is not None:
                user_input = Prompt.ask("\n[bold green]kali-ai[/bold green]")
            else:
                user_input = input("\nkali-ai> ")

            user_input = user_input.strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print_msg("Goodbye!", style="yellow")
                break

            messages.append({"role": "user", "content": user_input})
            run_chat_turn(client, cfg["model"], messages, auto_approve=args.yes)

        except (KeyboardInterrupt, EOFError):
            print_msg("\nSession ended.", style="yellow")
            break


if __name__ == "__main__":
    main()
