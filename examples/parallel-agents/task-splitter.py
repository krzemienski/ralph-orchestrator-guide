#!/usr/bin/env python3
"""
Task Splitter for Ralph Parallel Agents

Decomposes a high-level objective into individual tasks that can be
distributed across parallel agent worktrees.

Usage:
    python task-splitter.py "Build the user dashboard" --output tasks.jsonl
    python task-splitter.py --from-plan plan.md --output tasks.jsonl
    ralph run --config parallel.toml --tasks tasks.jsonl
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def create_task(task_id: str, title: str, description: str,
                dependencies: list[str] | None = None,
                priority: int = 0) -> dict:
    """Create a single task entry for the JSONL task file."""
    return {
        "id": task_id,
        "title": title,
        "description": description,
        "status": "pending",
        "priority": priority,
        "dependencies": dependencies or [],
        "assigned_to": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }


def split_from_objective(objective: str) -> list[dict]:
    """
    Split a high-level objective into tasks.

    In production, this would call an LLM to decompose the objective.
    This example shows the structure with manual decomposition.
    """
    # Example decomposition — replace with LLM-based splitting for real use
    tasks = [
        create_task(
            "task-001",
            "Set up project structure",
            f"Create the initial project structure for: {objective}\n"
            "- Initialize package.json / Cargo.toml / etc.\n"
            "- Set up directory structure\n"
            "- Configure build system",
            priority=0,
        ),
        create_task(
            "task-002",
            "Implement core data models",
            "Define the data models and types needed for the feature.\n"
            "- Create type definitions\n"
            "- Add validation logic\n"
            "- Document the schema",
            dependencies=["task-001"],
            priority=1,
        ),
        create_task(
            "task-003",
            "Build API endpoints",
            "Implement the API layer for the feature.\n"
            "- Create route handlers\n"
            "- Add request validation\n"
            "- Implement error handling",
            dependencies=["task-002"],
            priority=1,
        ),
        create_task(
            "task-004",
            "Build UI components",
            "Create the frontend components for the feature.\n"
            "- Build reusable components\n"
            "- Add responsive styling\n"
            "- Wire up to API endpoints",
            dependencies=["task-002"],
            priority=1,
        ),
        create_task(
            "task-005",
            "Integration and validation",
            "Verify the complete feature works end-to-end.\n"
            "- Test all API endpoints\n"
            "- Verify UI renders correctly\n"
            "- Check error handling paths",
            dependencies=["task-003", "task-004"],
            priority=2,
        ),
    ]
    return tasks


def split_from_plan(plan_path: str) -> list[dict]:
    """
    Split tasks from an existing plan document.

    Reads a markdown plan and extracts task entries.
    Looks for headers (##) and checkbox items (- [ ]).
    """
    path = Path(plan_path)
    if not path.exists():
        print(f"Error: Plan file not found: {plan_path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()
    tasks = []
    task_num = 1
    current_section = ""

    for line in content.split("\n"):
        line = line.strip()

        # Track section headers
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue

        # Extract tasks from checkboxes
        if line.startswith("- [ ] ") or line.startswith("- [x] "):
            title = line[6:].strip()
            tasks.append(create_task(
                f"task-{task_num:03d}",
                title,
                f"From section: {current_section}\n\nTask: {title}",
                priority=task_num,
            ))
            task_num += 1

    if not tasks:
        print("Warning: No tasks found in plan. Looking for '- [ ]' checkboxes.",
              file=sys.stderr)

    return tasks


def write_tasks(tasks: list[dict], output_path: str) -> None:
    """Write tasks as JSONL (one JSON object per line)."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        for task in tasks:
            f.write(json.dumps(task) + "\n")

    print(f"Wrote {len(tasks)} tasks to {output_path}")
    for task in tasks:
        deps = f" (depends: {', '.join(task['dependencies'])})" if task['dependencies'] else ""
        print(f"  [{task['id']}] {task['title']}{deps}")


def main():
    parser = argparse.ArgumentParser(
        description="Split objectives into parallel tasks for Ralph"
    )
    parser.add_argument(
        "objective",
        nargs="?",
        help="High-level objective to decompose into tasks"
    )
    parser.add_argument(
        "--from-plan",
        help="Path to a markdown plan file to extract tasks from"
    )
    parser.add_argument(
        "--output", "-o",
        default="tasks.jsonl",
        help="Output path for the JSONL task file (default: tasks.jsonl)"
    )

    args = parser.parse_args()

    if args.from_plan:
        tasks = split_from_plan(args.from_plan)
    elif args.objective:
        tasks = split_from_objective(args.objective)
    else:
        parser.print_help()
        sys.exit(1)

    write_tasks(tasks, args.output)


if __name__ == "__main__":
    main()
