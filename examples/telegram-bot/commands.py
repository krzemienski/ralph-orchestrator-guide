#!/usr/bin/env python3
"""
Telegram Command Handlers for Ralph Orchestrator

Example implementation of Telegram bot commands for monitoring
and controlling Ralph agent loops remotely.

Usage:
    This module is loaded by Ralph's telegram integration.
    For standalone testing: python commands.py --test

Dependencies:
    pip install python-telegram-bot>=20.0
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Ralph state file locations
RALPH_DIR = Path(".ralph")
LOOP_STATE = RALPH_DIR / "loop-state.json"
MEMORIES = RALPH_DIR / "agent" / "memories.md"
TASKS = RALPH_DIR / "agent" / "tasks.jsonl"
MERGE_QUEUE = RALPH_DIR / "merge-queue.jsonl"
METRICS = RALPH_DIR / "metrics.json"
GUIDANCE_FILE = RALPH_DIR / "guidance.jsonl"
PAUSE_FLAG = RALPH_DIR / "pause.flag"


def read_state() -> dict[str, Any]:
    """Read the current loop state."""
    if not LOOP_STATE.exists():
        return {"status": "not_running", "iteration": 0}
    return json.loads(LOOP_STATE.read_text())


def read_metrics() -> dict[str, Any]:
    """Read accumulated metrics."""
    if not METRICS.exists():
        return {"total_tokens": 0, "total_cost": 0.0, "iterations": 0}
    return json.loads(METRICS.read_text())


def read_tasks() -> list[dict]:
    """Read all tasks from the JSONL task file."""
    if not TASKS.exists():
        return []
    tasks = []
    for line in TASKS.read_text().strip().split("\n"):
        if line.strip():
            tasks.append(json.loads(line))
    return tasks


def read_recent_logs(n: int = 10) -> list[str]:
    """Read the last N log entries."""
    log_dir = RALPH_DIR / "logs"
    if not log_dir.exists():
        return ["No logs found."]

    log_files = sorted(log_dir.glob("*.log"), reverse=True)
    if not log_files:
        return ["No log files found."]

    lines = log_files[0].read_text().strip().split("\n")
    return lines[-n:]


# =============================================================================
# Command Handlers
# =============================================================================

def cmd_status() -> str:
    """
    /status — Show current loop state.

    Returns: iteration count, current hat, elapsed time, task progress.
    """
    state = read_state()

    if state.get("status") == "not_running":
        return "No active loop. Start one with `ralph run`."

    tasks = read_tasks()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    pending = sum(1 for t in tasks if t.get("status") == "pending")
    in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")

    started = state.get("started_at", "unknown")
    elapsed = ""
    if started != "unknown":
        try:
            start_time = datetime.fromisoformat(started)
            delta = datetime.now(timezone.utc) - start_time
            minutes = int(delta.total_seconds() / 60)
            elapsed = f" ({minutes}m elapsed)"
        except (ValueError, TypeError):
            pass

    paused = " [PAUSED]" if PAUSE_FLAG.exists() else ""

    return (
        f"Status: {state.get('status', 'unknown')}{paused}{elapsed}\n"
        f"Iteration: {state.get('iteration', 0)}/{state.get('max_iterations', '?')}\n"
        f"Hat: {state.get('current_hat', 'none')}\n"
        f"Tasks: {completed}/{total} done, {in_progress} active, {pending} pending"
    )


def cmd_pause() -> str:
    """
    /pause — Pause the loop after the current iteration completes.

    Creates a pause flag file that the loop checks between iterations.
    """
    PAUSE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    PAUSE_FLAG.write_text(datetime.now(timezone.utc).isoformat())
    return "Loop will pause after the current iteration completes."


def cmd_resume() -> str:
    """
    /resume — Resume a paused loop.

    Removes the pause flag file.
    """
    if PAUSE_FLAG.exists():
        PAUSE_FLAG.unlink()
        return "Loop resumed."
    return "Loop is not paused."


def cmd_approve() -> str:
    """
    /approve — Approve a pending human.interact request.

    Writes an approval response that the agent reads on next iteration.
    """
    response = {
        "type": "approval",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Approved via Telegram",
    }
    _write_guidance(response)
    return "Approved. Agent will continue on next iteration."


def cmd_reject(reason: str = "") -> str:
    """
    /reject [reason] — Reject a pending request with feedback.

    The reason is passed to the agent as guidance for its next iteration.
    """
    response = {
        "type": "rejection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": reason or "Rejected via Telegram (no reason given)",
    }
    _write_guidance(response)
    return f"Rejected. Agent will receive feedback: {reason or '(no reason)'}"


def cmd_metrics() -> str:
    """
    /metrics — Show token usage, cost, and timing statistics.
    """
    m = read_metrics()
    return (
        f"Tokens: {m.get('total_tokens', 0):,}\n"
        f"Cost: ${m.get('total_cost', 0.0):.4f}\n"
        f"Iterations: {m.get('iterations', 0)}\n"
        f"Avg tokens/iter: {m.get('avg_tokens_per_iteration', 0):,.0f}\n"
        f"Avg cost/iter: ${m.get('avg_cost_per_iteration', 0.0):.4f}"
    )


def cmd_kill() -> str:
    """
    /kill — Force-stop the loop immediately.

    Writes a kill signal and removes the loop lock.
    """
    kill_file = RALPH_DIR / "kill.signal"
    kill_file.parent.mkdir(parents=True, exist_ok=True)
    kill_file.write_text(datetime.now(timezone.utc).isoformat())
    return "Kill signal sent. Loop will terminate."


def cmd_guidance(text: str) -> str:
    """
    /guidance [text] — Send guidance to the agent.

    Guidance is injected as a `## ROBOT GUIDANCE` section in the agent's
    next prompt. Multiple guidance messages are squashed into a numbered list.
    """
    if not text.strip():
        return "Usage: /guidance <your message to the agent>"

    response = {
        "type": "guidance",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": text.strip(),
    }
    _write_guidance(response)
    return f"Guidance sent. Agent will receive it on next iteration."


def cmd_logs(n: int = 10) -> str:
    """
    /logs [n] — Show the last N log entries.
    """
    lines = read_recent_logs(n)
    return "\n".join(lines)


# =============================================================================
# Helpers
# =============================================================================

def _write_guidance(entry: dict) -> None:
    """Append a guidance entry to the JSONL guidance file."""
    GUIDANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GUIDANCE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# Command dispatch table
COMMANDS = {
    "status": cmd_status,
    "pause": cmd_pause,
    "resume": cmd_resume,
    "approve": cmd_approve,
    "reject": cmd_reject,
    "metrics": cmd_metrics,
    "kill": cmd_kill,
    "guidance": cmd_guidance,
    "logs": cmd_logs,
}


def dispatch(command: str, args: str = "") -> str:
    """Dispatch a command string to the appropriate handler."""
    handler = COMMANDS.get(command)
    if not handler:
        return f"Unknown command: /{command}\nAvailable: {', '.join(COMMANDS.keys())}"

    if command in ("reject", "guidance"):
        return handler(args)
    elif command == "logs":
        try:
            n = int(args) if args else 10
        except ValueError:
            n = 10
        return handler(n)
    else:
        return handler()


# =============================================================================
# Standalone Testing
# =============================================================================

if __name__ == "__main__":
    if "--test" in sys.argv:
        print("Testing command handlers...\n")
        for cmd_name in COMMANDS:
            print(f"/{cmd_name}:")
            result = dispatch(cmd_name, "test reason" if cmd_name in ("reject", "guidance") else "")
            print(f"  {result}\n")
    else:
        # Interactive mode
        print("Ralph Telegram Commands — Interactive Mode")
        print("Type commands like: status, pause, metrics, guidance hello agent")
        print("Type 'quit' to exit.\n")
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if user_input in ("quit", "exit"):
                break
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lstrip("/")
            args = parts[1] if len(parts) > 1 else ""
            print(dispatch(cmd, args))
            print()
