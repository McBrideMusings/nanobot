# Workspace

All agent state lives in the workspace directory. By default: `~/.nanobot/workspace/`.

## Structure

```
~/.nanobot/
├── config.json              # Main configuration
├── sessions/                # Conversation history (JSONL)
│   ├── telegram_123456.jsonl
│   ├── api_default.jsonl
│   └── ...
├── cron/
│   └── jobs.json            # Scheduled tasks
└── workspace/
    ├── SOUL.md              # Agent personality
    ├── USER.md              # User information
    ├── AGENTS.md            # Behavioral instructions
    ├── TOOLS.md             # Tool reference
    ├── IDENTITY.md          # Hard identity (optional)
    ├── HEARTBEAT.md         # Periodic tasks
    ├── memory/
    │   ├── MEMORY.md        # Long-term memory
    │   └── YYYY-MM-DD.md    # Daily notes
    └── skills/
        └── my-skill/
            └── SKILL.md     # Custom skill definition
```

## Bootstrap Files

These files are loaded into the system prompt every time the agent responds:

| File | Purpose |
|------|---------|
| `SOUL.md` | Personality, values, communication style |
| `USER.md` | Info about the user (name, timezone, preferences) |
| `AGENTS.md` | Operational instructions (how to use tools, memory, heartbeat) |
| `TOOLS.md` | Tool reference documentation |
| `IDENTITY.md` | Core identity anchor (optional) |

## Memory System

**Long-term memory** (`memory/MEMORY.md`):
- Facts, preferences, and context learned over time
- Loaded into system prompt
- Agent updates via `write_file` / `edit_file`

**Daily notes** (`memory/YYYY-MM-DD.md`):
- Timestamped entries from each day
- Recent days loaded into context
- Older notes fall out of context window (see [Memory Search](/tickets/12) for planned search)

## Heartbeat

`HEARTBEAT.md` is checked every 30 minutes by the heartbeat service. The agent reads it, executes any tasks, and responds.

Example:

```markdown
- Browse the internet for interesting tech news
- Only DM me if something is genuinely surprising or useful
```

See [Heartbeat Enhancements](/tickets/14) for planned improvements.

## Sessions

Session files are JSONL format — one JSON object per line:
- First line: metadata (created_at, updated_at)
- Remaining lines: messages (role, content, timestamp)

Sessions are keyed by `channel:chat_id`. The agent loads the last 50 messages from the session file, then truncates from oldest first to fit within the model's context window. See [Agent Loop — Context Window Management](/architecture/agent-loop#context-window-management) for details.

## Security

When `tools.restrictToWorkspace` is `true`:
- File tools are sandboxed to the workspace directory
- Shell commands can't access paths outside workspace
- Path traversal (`../`) is blocked
