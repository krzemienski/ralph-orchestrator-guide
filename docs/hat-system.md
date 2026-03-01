# The Hat System: Context as a First-Class Concept

The hat system is Ralph's most distinctive architectural decision. Instead of giving an agent a monolithic prompt, Ralph decomposes work into focused roles — "hats" — that an agent wears during a single iteration.

## How Hats Work

### The HatlessRalph Coordinator

A `HatlessRalph` coordinator is always present as the universal fallback. It holds:
- The current objective
- The hat topology (which hats exist and how they connect)
- Skill indices
- Human guidance from Telegram

When a new iteration begins, the coordinator selects which hat the agent should wear based on the current event bus state.

### Hat Anatomy

Each hat carries five components:

| Component | Purpose |
|-----------|---------|
| **Name + Description** | Identifies the role (e.g., "planner", "coder", "reviewer") |
| **Subscriptions** | Which events trigger this hat (e.g., `plan.complete`) |
| **Publications** | Which events this hat can emit (e.g., `code.complete`) |
| **Instructions** | The specialized prompt injected when wearing this hat |
| **Event Receivers** | Map showing what downstream hats each publication activates |

### Event-Driven Transitions

Hats form a directed graph connected by events:

```
planner                    coder                     reviewer
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Subscribes:     │       │ Subscribes:     │       │ Subscribes:     │
│   project.start │──────>│   plan.complete │──────>│   code.complete │
│                 │       │                 │       │                 │
│ Publishes:      │       │ Publishes:      │       │ Publishes:      │
│   plan.complete │       │   code.complete │       │   review.pass   │
│   human.interact│       │   human.interact│       │   review.fail   │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                    ↑                         │
                                    └─── review.fail ─────────┘
```

When a `planner` hat publishes `plan.complete`, the coordinator knows to transition to the `coder` hat. When the `reviewer` publishes `review.fail`, the coordinator routes back to `coder`.

## Configuring Hats

### TOML Configuration

```toml
[hats.planner]
description = "Plans the implementation approach"
model = "opus"                     # Use strongest model for planning
subscribes = ["project.start", "review.fail"]
publishes = ["plan.complete", "human.interact"]
instructions = """
You are a technical planner. Analyze the objective and create
a step-by-step implementation plan. Consider edge cases,
dependencies, and potential blockers.
"""

[hats.coder]
description = "Implements the plan"
model = "sonnet"                   # Balanced model for implementation
subscribes = ["plan.complete"]
publishes = ["code.complete", "human.interact"]
instructions = """
You are an implementation engineer. Follow the plan exactly.
Build one component at a time. Verify the build after each change.
"""

[hats.reviewer]
description = "Reviews code quality and correctness"
model = "opus"                     # Strong model for review
subscribes = ["code.complete"]
publishes = ["review.pass", "review.fail"]
instructions = """
You are a code reviewer. Check for bugs, security issues,
performance problems, and adherence to the plan. Be specific
in your feedback.
"""
```

### Per-Project Hat Topologies

Different project types benefit from different hat graphs:

**Web Frontend:**
```
designer → coder → reviewer → deployer
```

**Systems / Backend:**
```
architect → coder → tester → security-reviewer → deployer
```

**Data Pipeline:**
```
schema-designer → pipeline-builder → validator → documenter
```

**Bug Fix:**
```
investigator → fixer → tester → reviewer
```

## Why Fresh Context Matters

Ralph's first tenet — **Fresh Context Is Reliability** — is directly enabled by the hat system.

Each iteration clears context. The agent re-reads specs, plans, and code every cycle. The hat system ensures that each fresh-context iteration has a focused, well-scoped objective rather than a vague "continue working on the project."

**Long context (150K tokens accumulated):**
- Agent loses track of earlier decisions
- Contradictions accumulate in context
- Quality degrades as context fills

**Fresh context (40K tokens, hat-scoped):**
- Agent reads only what the current hat needs
- No accumulated contradictions
- Consistent quality across iterations

## Model Routing per Hat

Different hats can use different models:

| Hat | Recommended Model | Reasoning |
|-----|-------------------|-----------|
| Planner | Opus | Deep reasoning for architecture decisions |
| Coder | Sonnet | Balanced speed/quality for implementation |
| Reviewer | Opus | Thorough analysis catches subtle bugs |
| Documenter | Haiku | Fast output for straightforward writing |
| Investigator | Sonnet | Good at code search and pattern matching |

This optimizes cost: you only use expensive models where deep reasoning matters.

## Hat Best Practices

1. **Keep hats focused.** A hat that plans AND codes AND reviews is just a monolithic prompt with extra steps.

2. **Define clear event boundaries.** Every hat should know exactly what triggers it and what it produces.

3. **Use the event publishing guide.** Tell the agent what happens when it publishes each event — which hat picks up next and what that hat expects.

4. **Let the coordinator decide transitions.** Don't hardcode hat sequences in prompts. Let the event bus drive transitions.

5. **Start simple.** A `planner → coder → reviewer` graph handles most projects. Add hats when you identify specific quality gaps.
