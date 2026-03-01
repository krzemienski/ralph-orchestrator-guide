#!/usr/bin/env bash
# Ralph Stop Hook — "The Boulder Never Stops"
#
# This script runs when a stop signal is received (session end, timeout, etc.)
# It checks if there are remaining tasks. If tasks remain, it injects
# "The boulder never stops" into the agent's next prompt, causing the
# loop to continue.
#
# Usage: Called automatically by Ralph's loop.stop_hook configuration
#        Can also be tested manually: bash stop-hook.sh
#
# Exit behavior:
#   Outputs "continue" → loop keeps running
#   Outputs "stop" → loop terminates

set -euo pipefail

STATE_FILE=".ralph/loop-state.json"
TASKS_FILE=".ralph/agent/tasks.jsonl"
GUIDANCE_FILE=".ralph/guidance.jsonl"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
    echo "stop"
    exit 0
fi

# Count remaining tasks
if [ -f "$TASKS_FILE" ]; then
    PENDING=$(grep -c '"status":\s*"pending"' "$TASKS_FILE" 2>/dev/null || echo "0")
    IN_PROGRESS=$(grep -c '"status":\s*"in_progress"' "$TASKS_FILE" 2>/dev/null || echo "0")
    REMAINING=$((PENDING + IN_PROGRESS))
else
    REMAINING=0
fi

# Check for explicit kill signal
if [ -f ".ralph/kill.signal" ]; then
    echo "Kill signal detected. Stopping." >&2
    rm -f ".ralph/kill.signal"
    echo "stop"
    exit 0
fi

# Check for pause flag
if [ -f ".ralph/pause.flag" ]; then
    echo "Pause flag detected. Stopping (resume with /resume)." >&2
    echo "stop"
    exit 0
fi

# The boulder never stops — if tasks remain, keep going
if [ "$REMAINING" -gt 0 ]; then
    echo "Tasks remaining: $REMAINING. The boulder never stops." >&2

    # Inject continuation guidance
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$GUIDANCE_FILE")"
    echo "{\"type\":\"continuation\",\"timestamp\":\"$TIMESTAMP\",\"message\":\"The boulder never stops. $REMAINING tasks remain. Continue working.\"}" >> "$GUIDANCE_FILE"

    echo "continue"
    exit 0
fi

# All tasks complete — stop gracefully
echo "All tasks complete. Loop can stop." >&2
echo "stop"
exit 0
