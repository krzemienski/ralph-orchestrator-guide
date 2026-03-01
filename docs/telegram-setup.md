# Telegram Setup Guide

Step-by-step instructions for connecting Ralph Orchestrator to Telegram for remote monitoring and control.

**Time required:** 5 minutes

---

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name for your bot (e.g., "Ralph Monitor")
4. Choose a username (e.g., `ralph_monitor_bot` — must end in `bot`)
5. BotFather will give you a token like: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`
6. **Save this token** — you'll need it in Step 3

## Step 2: Get Your Chat ID

1. Search for `@userinfobot` on Telegram
2. Send it any message
3. It will reply with your user info including your **Chat ID** (a number like `987654321`)
4. **Save this Chat ID** — you'll need it in Step 3

> **For group chats:** Add `@userinfobot` to the group temporarily. The group chat ID will be negative (e.g., `-1001234567890`).

## Step 3: Set Environment Variables

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export RALPH_TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
export RALPH_TELEGRAM_CHAT_ID="987654321"

# Reload your shell
source ~/.zshrc
```

> **Security:** Never commit these values to git. The bot token grants full control of your bot.

## Step 4: Register Bot Commands (Optional but Recommended)

Tell BotFather about your commands so Telegram shows them in the command menu:

1. Message `@BotFather`
2. Send `/setcommands`
3. Select your bot
4. Send this list:

```
status - Current loop state and progress
pause - Pause after current iteration
resume - Resume a paused loop
approve - Approve a pending question
reject - Reject with feedback
metrics - Token usage and cost stats
kill - Force stop the loop
guidance - Send guidance to the agent
logs - Show recent log entries
```

## Step 5: Test the Connection

```bash
# Verify the bot can send you a message
curl -s "https://api.telegram.org/bot${RALPH_TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${RALPH_TELEGRAM_CHAT_ID}" \
  -d "text=Ralph bot connected successfully!" \
  | python3 -m json.tool

# You should receive a message on Telegram
```

## Step 6: Start Ralph with Telegram

```bash
# Using the example config
ralph run \
  --config examples/basic-loop/loop.toml \
  --telegram examples/telegram-bot/bot-config.toml \
  "Build the user dashboard"

# Or with a hat
ralph run \
  --hat configs/web-frontend.toml \
  --telegram examples/telegram-bot/bot-config.toml \
  "Implement responsive navigation"
```

---

## Using the Bot

### Checking Status
Send `/status` to your bot:
```
Status: running (45m elapsed)
Iteration: 12/50
Hat: coder
Tasks: 3/8 done, 1 active, 4 pending
```

### Sending Guidance
Send `/guidance Focus on the API first`:
```
Guidance sent. Agent will receive it on next iteration.
```

The agent sees this in its next prompt:
```markdown
## ROBOT GUIDANCE
1. Focus on the API first
```

### Approving Agent Questions
When the agent needs a decision:
```
NEEDS INPUT — systems
Question: Should I use PostgreSQL or SQLite for the cache layer?
Reply to approve, or send guidance.
```

Reply `/approve` to accept the agent's proposed approach, or `/guidance Use SQLite for simplicity`.

### Emergency Stop
Send `/kill` to immediately terminate the loop:
```
Kill signal sent. Loop will terminate.
```

---

## Troubleshooting

### Bot doesn't respond
- Verify token: `curl "https://api.telegram.org/bot${RALPH_TELEGRAM_BOT_TOKEN}/getMe"`
- Verify chat ID: Send a message to the bot, then check: `curl "https://api.telegram.org/bot${RALPH_TELEGRAM_BOT_TOKEN}/getUpdates"`
- Make sure you've started the Ralph loop with `--telegram`

### Messages not arriving
- Check the notification settings in `bot-config.toml` — some events may be disabled
- Verify the chat ID is correct (personal vs. group)
- Check Ralph logs at `.ralph/logs/` for send failures

### Wrong chat receiving messages
- Group chat IDs are negative numbers
- Personal chat IDs are positive numbers
- Update `RALPH_TELEGRAM_CHAT_ID` if you switched between personal and group

### Rate limiting
- Telegram limits bots to ~30 messages/second
- Ralph batches notifications to stay under limits
- If you hit limits, reduce `checkpoint_interval` to send fewer updates
