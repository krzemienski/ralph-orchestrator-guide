# Basic Loop Example

The simplest Ralph configuration — one agent working in a loop until the task is done.

## How to Run

```bash
# Start a basic loop with a task description
ralph run --config loop.toml "Fix the login page CSS alignment"

# With a specific hat for more context
ralph run --config loop.toml --hat ../../configs/web-frontend.toml "Fix the login page CSS alignment"
```

## What Happens

1. Ralph starts the agent with your task description
2. The agent reads `instructions.md` for behavioral guidance
3. Each iteration:
   - Agent reads its memories from previous iterations
   - Makes progress on the task (edits files, runs commands)
   - Writes a memory entry recording what it did
   - Build backpressure gate runs (`npm run build`)
4. When the agent emits `LOOP_COMPLETE`, the loop ends
5. If `max_iterations` (20) is reached, the loop stops with exit code 2

## Files

| File | Purpose |
|------|---------|
| `loop.toml` | Loop configuration (iterations, timeout, backpressure) |
| `instructions.md` | Agent behavioral instructions |

## Customizing

- Change `max_iterations` for longer/shorter tasks
- Add more backpressure gates (lint, test, typecheck)
- Modify `instructions.md` for different agent behavior
- Point `index_dirs` at your project's source directories
