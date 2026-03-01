#!/usr/bin/env python3
"""
State Manager for Ralph Persistence Loops

Manages the loop state file that enables session persistence and
resume-from-checkpoint behavior.

Usage:
    python state-manager.py status          # Show current state
    python state-manager.py checkpoint      # Force a checkpoint
    python state-manager.py resume          # Resume from last checkpoint
    python state-manager.py reset           # Clear state (fresh start)
    python state-manager.py history         # Show checkpoint history
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RALPH_DIR = Path(".ralph")
STATE_FILE = RALPH_DIR / "loop-state.json"
HISTORY_FILE = RALPH_DIR / "state-history.jsonl"
TASKS_FILE = RALPH_DIR / "agent" / "tasks.jsonl"


def read_state() -> dict[str, Any]:
    """Read the current loop state from disk."""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        print(f"Warning: Corrupted state file at {STATE_FILE}", file=sys.stderr)
        return {}


def write_state(state: dict[str, Any]) -> None:
    """Write loop state to disk atomically."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first, then rename (atomic on POSIX)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(STATE_FILE)


def append_history(state: dict[str, Any]) -> None:
    """Append a state snapshot to the history log."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "state": state,
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_task_summary() -> dict[str, int]:
    """Summarize task statuses from the JSONL task file."""
    summary = {"total": 0, "pending": 0, "in_progress": 0, "completed": 0}
    if not TASKS_FILE.exists():
        return summary

    for line in TASKS_FILE.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            task = json.loads(line)
            summary["total"] += 1
            status = task.get("status", "pending")
            if status in summary:
                summary[status] += 1
        except json.JSONDecodeError:
            continue

    return summary


# =============================================================================
# Commands
# =============================================================================

def cmd_status() -> None:
    """Show the current loop state."""
    state = read_state()
    if not state:
        print("No active loop state found.")
        print(f"State file: {STATE_FILE}")
        return

    print("=== Ralph Loop State ===")
    print(f"Status:     {state.get('status', 'unknown')}")
    print(f"Iteration:  {state.get('iteration', 0)}/{state.get('max_iterations', '?')}")
    print(f"Hat:        {state.get('current_hat', 'none')}")
    print(f"Started:    {state.get('started_at', 'unknown')}")
    print(f"Updated:    {state.get('updated_at', 'unknown')}")

    # Calculate elapsed time
    started = state.get("started_at")
    if started:
        try:
            start_time = datetime.fromisoformat(started)
            elapsed = datetime.now(timezone.utc) - start_time
            hours = int(elapsed.total_seconds() / 3600)
            minutes = int((elapsed.total_seconds() % 3600) / 60)
            print(f"Elapsed:    {hours}h {minutes}m")
        except (ValueError, TypeError):
            pass

    # Task summary
    tasks = get_task_summary()
    if tasks["total"] > 0:
        print(f"\nTasks:      {tasks['completed']}/{tasks['total']} complete")
        print(f"  Pending:     {tasks['pending']}")
        print(f"  In Progress: {tasks['in_progress']}")
        print(f"  Completed:   {tasks['completed']}")

    # Cost tracking
    cost = state.get("total_cost", 0)
    tokens = state.get("total_tokens", 0)
    if cost or tokens:
        print(f"\nTokens:     {tokens:,}")
        print(f"Cost:       ${cost:.4f}")


def cmd_checkpoint() -> None:
    """Force a checkpoint save of the current state."""
    state = read_state()
    if not state:
        print("No active state to checkpoint.")
        return

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["checkpoint_type"] = "manual"

    write_state(state)
    append_history(state)

    print(f"Checkpoint saved at iteration {state.get('iteration', 0)}")
    print(f"State file: {STATE_FILE}")
    print(f"History: {HISTORY_FILE}")


def cmd_resume() -> None:
    """Show what would happen on resume."""
    state = read_state()
    if not state:
        print("No state to resume from. Run `ralph run` to start fresh.")
        return

    print("=== Resume Info ===")
    print(f"Would resume from iteration {state.get('iteration', 0)}")
    print(f"Last hat: {state.get('current_hat', 'none')}")
    print(f"Last updated: {state.get('updated_at', 'unknown')}")

    tasks = get_task_summary()
    remaining = tasks["pending"] + tasks["in_progress"]
    print(f"Remaining tasks: {remaining}")

    print(f"\nTo resume: ralph run --config persistence.toml --resume")


def cmd_reset() -> None:
    """Clear all state (fresh start)."""
    removed = []
    for f in [STATE_FILE, RALPH_DIR / "pause.flag", RALPH_DIR / "kill.signal"]:
        if f.exists():
            f.unlink()
            removed.append(str(f))

    if removed:
        print("Cleared state files:")
        for f in removed:
            print(f"  {f}")
    else:
        print("No state files to clear.")

    print("\nNote: Memories and task history are preserved.")
    print("To fully reset, also delete .ralph/agent/")


def cmd_history() -> None:
    """Show checkpoint history."""
    if not HISTORY_FILE.exists():
        print("No checkpoint history found.")
        return

    entries = []
    for line in HISTORY_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not entries:
        print("No checkpoint entries.")
        return

    print(f"=== Checkpoint History ({len(entries)} entries) ===\n")
    for entry in entries[-20:]:  # Show last 20
        ts = entry.get("timestamp", "unknown")
        state = entry.get("state", {})
        iteration = state.get("iteration", "?")
        hat = state.get("current_hat", "?")
        cp_type = state.get("checkpoint_type", "auto")
        print(f"  [{ts}] iter={iteration} hat={hat} type={cp_type}")

    if len(entries) > 20:
        print(f"\n  ... and {len(entries) - 20} earlier entries")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Ralph Loop State Manager")
    parser.add_argument(
        "command",
        choices=["status", "checkpoint", "resume", "reset", "history"],
        help="Command to run"
    )

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "checkpoint": cmd_checkpoint,
        "resume": cmd_resume,
        "reset": cmd_reset,
        "history": cmd_history,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
