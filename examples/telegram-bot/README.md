# Telegram Bot Example

Control Ralph agent loops from your phone using Telegram as a remote control plane.

## Setup

See [docs/telegram-setup.md](../../docs/telegram-setup.md) for the full step-by-step guide.

Quick version:
1. Message `@BotFather` on Telegram, create a bot, get the token
2. Message `@userinfobot` to get your chat ID
3. Set environment variables:
   ```bash
   export RALPH_TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
   export RALPH_TELEGRAM_CHAT_ID="987654321"
   ```

## Usage

```bash
# Start a loop with Telegram integration
ralph run --config ../basic-loop/loop.toml --telegram bot-config.toml "Build the feature"
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/status` | Current loop state, iteration count, hat, task progress |
| `/pause` | Pause the loop after the current iteration |
| `/resume` | Resume a paused loop |
| `/approve` | Approve a pending agent question |
| `/reject [reason]` | Reject with feedback |
| `/metrics` | Token usage, cost, timing statistics |
| `/kill` | Force-stop the loop immediately |
| `/guidance [text]` | Send guidance injected into the agent's next prompt |
| `/logs [n]` | Show last N log entries |

## Interaction Patterns

### Agent-to-Human (`human.interact`)

When the agent hits a decision it can't make autonomously, it sends you a Telegram message and **blocks** until you respond or the timeout (300s) expires.

```
NEEDS INPUT — ios-mobile
Question: Should I use NavigationStack or NavigationSplitView for the settings screen?
Reply to approve, or send guidance.
```

### Human-to-Agent (`human.guidance`)

Proactive messages you send are injected as `## ROBOT GUIDANCE` in the agent's next prompt:

```
You: /guidance Focus on the API endpoints first, skip the UI for now
Bot: Guidance sent. Agent will receive it on next iteration.
```

## Files

| File | Purpose |
|------|---------|
| `bot-config.toml` | Telegram bot configuration (token, chat ID, commands) |
| `commands.py` | Command handler implementations |
