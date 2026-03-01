# Parallel Agents Example

Run multiple Ralph agents simultaneously, each in an isolated git worktree, with changes flowing through an event-sourced merge queue.

## How It Works

```
Main Branch ─────────────────────────────────────────────> (merged)
     │                                                        ↑
     ├─ Worktree 1 (task-001) ──── work ──── complete ─── merge ─┤
     ├─ Worktree 2 (task-002) ──── work ──── complete ─── merge ─┤
     ├─ Worktree 3 (task-003) ──── work ──── complete ─── merge ─┤
     └─ Worktree 4 (task-004) ──── work ──── complete ─── merge ─┘
```

Each agent:
1. Gets its own git worktree (full filesystem isolation)
2. Works independently on its assigned task
3. Shares memories and specs via symlinks
4. Enqueues completed work into the merge queue
5. The primary loop processes merges sequentially

## Quick Start

```bash
# 1. Generate tasks from an objective
python task-splitter.py "Build a user authentication system" -o tasks.jsonl

# 2. Run parallel agents
ralph run --config parallel.toml --parallel 4 --tasks tasks.jsonl

# 3. Monitor progress
ralph status
```

## Files

| File | Purpose |
|------|---------|
| `parallel.toml` | Parallel execution config (workers, merge queue, isolation) |
| `task-splitter.py` | Decomposes objectives into distributable tasks |

## Task File Format (JSONL)

Each line is a JSON object:

```json
{"id": "task-001", "title": "Set up project", "status": "pending", "dependencies": []}
{"id": "task-002", "title": "Build models", "status": "pending", "dependencies": ["task-001"]}
```

Tasks with dependencies wait until their dependencies complete before being assigned.

## Merge Queue

The merge queue is an append-only JSONL log at `.ralph/merge-queue.jsonl`:

```json
{"type": "Queued",  "worktree": "task-001", "timestamp": "..."}
{"type": "Merging", "worktree": "task-001", "pid": 12345}
{"type": "Merged",  "worktree": "task-001", "commit": "abc123"}
```

File locking via `flock()` ensures concurrent access safety. The full history is preserved for debugging.
