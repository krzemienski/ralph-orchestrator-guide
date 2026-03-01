# The Six Tenets of Ralph Orchestrator

These tenets emerged from running 410+ orchestration sessions totaling over a gigabyte of interaction data. They are not theoretical principles — they are lessons learned from watching agents succeed and fail at scale.

---

## Tenet 1: The Boulder Never Stops

**Principle:** A Ralph loop continues working until all tasks are complete or an explicit kill signal is received. Session boundaries are checkpoints, not endpoints.

**In practice:**
- The stop hook checks for remaining tasks before allowing termination
- If tasks remain, the agent receives "The boulder never stops" and continues
- State is persisted to disk so loops survive session restarts
- Only explicit signals (`/kill`, `kill.signal` file) force-stop a running loop

**Why it matters:** AI agents in single sessions lose context at session boundaries. Ralph's persistence mechanism means work continues across sessions. A 50-task project doesn't need to be completed in one sitting.

**Example:**
```bash
# Session ends after iteration 20, but 30 tasks remain
# stop-hook.sh detects remaining tasks → injects continuation
# Next session resumes from iteration 21 with full memory
```

---

## Tenet 2: Hats Define Capability

**Principle:** An agent's role, tools, context, and event subscriptions are defined by the hat it wears. Changing the hat changes the agent's entire operational profile.

**In practice:**
- Each hat carries: name, subscriptions, publications, instructions, and tool permissions
- The `HatlessRalph` coordinator selects hats based on event bus state
- Hat transitions are logged and visible in the TUI, iOS app, and Telegram
- Custom hat graphs can be defined per project type

**Why it matters:** A monolithic prompt that tries to cover planning, coding, reviewing, and deploying produces mediocre results in all areas. Focused hats produce specialist-quality output in each area.

**Example hat graph:**
```
planner → coder → reviewer → deployer
    ↑         ↓
    └── fix ←─┘  (if review fails)
```

---

## Tenet 3: The Plan Is Disposable

**Principle:** Regenerating a plan costs one planning iteration. It is cheap. Never fight to save a plan that is not working.

**In practice:**
- Plans are stored in `.ralph/plans/` as versioned markdown
- When a plan hits a dead end, the agent regenerates from current state
- Cost of a new plan: ~$0.05 and 30 seconds. Cost of fighting a bad plan: hours of wasted iterations
- Event sourcing means the full planning history is preserved for learning

**Why it matters:** Sunk cost fallacy applies to AI-generated plans just as it applies to human plans. An agent that clings to a failing plan wastes tokens and time. An agent that regenerates quickly pivots to a better approach.

**When to discard a plan:**
- Build fails repeatedly after following the plan
- New information invalidates a core assumption
- The plan leads to unnecessary complexity
- More than 3 iterations without measurable progress

---

## Tenet 4: Telegram as Control Plane

**Principle:** The Telegram bot is not a notification system — it is a remote control plane for human-in-the-loop orchestration.

**In practice:**
- **Agent-to-Human:** Agent sends questions via Telegram and blocks until response
- **Human-to-Agent:** Guidance messages are injected into the agent's next prompt
- Commands (`/status`, `/pause`, `/approve`, `/kill`) provide real-time control
- The bot runs only on the primary loop; parallel loops route through it

**Why it matters:** When agents run overnight or in parallel, you need a way to steer them from your phone. Telegram provides a ubiquitous, mobile-first interface for checking status, sending corrections, and approving decisions — without touching a terminal.

**Interaction flow:**
```
Agent hits decision point → Sends Telegram message → Blocks event loop
Human reviews on phone → Sends reply or /approve → Agent continues
Timeout (300s) → Agent continues with default action
```

---

## Tenet 5: Worktrees as Isolation

**Principle:** Each parallel agent gets its own git worktree — full filesystem isolation with shared git history.

**In practice:**
- Worktrees created under `.worktrees/<loop-id>/`
- Memories, specs, and tasks symlinked back to main repo (shared knowledge)
- Each worktree has its own event bus, hat transitions, and iteration counter
- The merge queue (`merge-queue.jsonl`) coordinates worktree → main branch merges

**Why it matters:** Running 30 agents in the same directory causes immediate chaos — file overwrites, merge conflicts, corrupted state. Worktrees provide true filesystem isolation while preserving shared git history. The merge queue adds an orderly path from parallel work to unified codebase.

**Lifecycle:**
```
1. Create worktree → git worktree add .worktrees/loop-42 -b loop-42
2. Symlink shared files → memories, specs, tasks
3. Agent works independently in worktree
4. On completion → enqueue in merge-queue.jsonl
5. Primary loop merges → git merge --no-ff loop-42
6. Cleanup worktree → git worktree remove .worktrees/loop-42
```

---

## Tenet 6: QA Is Non-Negotiable

**Principle:** Backpressure gates (build, lint, test) reject bad work automatically. The agent figures out *how*; the gates ensure the result meets the bar.

**In practice:**
- Backpressure gates are defined in `[loop.backpressure]` in the TOML config
- Gates run after every iteration — build, lint, typecheck, test, security audit
- For subjective criteria, LLM-as-judge provides binary pass/fail
- Failed gates block the iteration from being marked complete

**Why it matters:** Telling an agent "write good code" is vague. Giving it a gate that runs `cargo clippy -- -D warnings` is precise. The agent has freedom in implementation but zero tolerance for quality failures. This is backpressure, not prescription.

**Example gates:**
```toml
[loop.backpressure]
build = "cargo build"
lint = "cargo clippy -- -D warnings"
test = "cargo test"
security = "cargo audit"
format = "cargo fmt --check"
```

**The philosophy:** Steer with signals, not scripts. When Ralph fails a specific way, the fix is not a more elaborate retry mechanism — it is a sign (a memory, a lint rule, a gate) that prevents the same failure next time.
