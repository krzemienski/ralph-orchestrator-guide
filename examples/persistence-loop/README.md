# Persistence Loop Example

A Ralph loop that survives session restarts and keeps working until all tasks are complete. Implements the first tenet: **"The boulder never stops."**

## How It Works

```
Session 1          Session 2          Session 3
│                  │                  │
├─ iter 1          ├─ iter 21         ├─ iter 41
├─ iter 2          ├─ iter 22         ├─ iter 42
├─ ...             ├─ ...             ├─ ...
├─ iter 20         ├─ iter 40         ├─ iter 50
├─ CHECKPOINT      ├─ CHECKPOINT      ├─ LOOP_COMPLETE
├─ session ends    ├─ session ends    └─ done!
│                  │
└─ stop-hook.sh    └─ stop-hook.sh
   "Tasks remain"     "Tasks remain"
   → CONTINUE         → CONTINUE
```

The stop hook checks for remaining tasks. If any exist, it injects "The boulder never stops" and the loop continues in the next session.

## Quick Start

```bash
# Start a persistent loop
ralph run --config persistence.toml "Complete all tasks in the backlog"

# Check state between sessions
python state-manager.py status

# Force a checkpoint
python state-manager.py checkpoint

# View checkpoint history
python state-manager.py history

# Reset to start fresh
python state-manager.py reset
```

## Files

| File | Purpose |
|------|---------|
| `persistence.toml` | Loop config with persistence enabled |
| `stop-hook.sh` | Checks tasks, continues if work remains |
| `state-manager.py` | CLI tool for inspecting and managing state |

## State Files

| File | Purpose |
|------|---------|
| `.ralph/loop-state.json` | Current iteration, hat, progress |
| `.ralph/state-history.jsonl` | Checkpoint history (append-only) |
| `.ralph/agent/memories.md` | Cross-iteration memories |
| `.ralph/agent/tasks.jsonl` | Task tracking |
| `.ralph/pause.flag` | Pause signal (create to pause) |
| `.ralph/kill.signal` | Kill signal (create to stop) |

## Manual Controls

```bash
# Pause the loop (stops after current iteration)
touch .ralph/pause.flag

# Resume
rm .ralph/pause.flag

# Force stop
touch .ralph/kill.signal
```
