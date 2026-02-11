# Development Setup

## Requirements

- Python 3.11+
- Node.js 18+ (only for WhatsApp bridge)
- Git

## Install from Source

```bash
git clone https://github.com/McBrideMusings/nanobot.git
cd nanobot
pip install -e ".[dev]"
```

## Commands

| Command | Description |
|---------|-------------|
| `pip install -e .` | Install from source |
| `pip install -e ".[dev]"` | Install with dev dependencies |
| `nanobot agent -m "msg"` | One-shot chat |
| `nanobot agent` | Interactive chat |
| `nanobot gateway` | Start gateway |
| `nanobot status` | Check providers |
| `pytest` | Run tests |
| `ruff check nanobot/` | Lint |

## Project Structure

```
nanobot/
├── agent/           # Core agent logic
│   ├── loop.py      # Agent loop (LLM ↔ tool execution)
│   ├── context.py   # Prompt builder
│   ├── memory.py    # Persistent memory
│   ├── skills.py    # Skills loader
│   ├── subagent.py  # Background tasks
│   └── tools/       # Built-in tools
├── skills/          # Bundled skills
├── channels/        # Chat integrations
├── bus/             # Message routing
├── cron/            # Scheduled tasks
├── heartbeat/       # Proactive wake-up
├── providers/       # LLM providers
├── session/         # Conversation state
├── config/          # Configuration schema
└── cli/             # CLI commands
```

## Ports

| Service | Port | Notes |
|---------|------|-------|
| Gateway / API WebSocket | 18790 | Configurable in config.json |
| vLLM (local models) | 8000 | External service |
| Docs (VitePress) | 5193 | `npm run docs:dev` |

## Environment Variables

Nanobot primarily uses `config.json` for configuration. Provider API keys are set in config and exported to environment variables at runtime for LiteLLM.

## Pierce's Infrastructure

| Component | Address |
|-----------|---------|
| Nanobot (Docker) | 100.114.249.118:18790 |
| vLLM backend | 100.114.249.118:8000 |
| Network | Tailscale (not public internet) |
| App data | /mnt/user/appdata/nanobot/ |
| Config | /mnt/user/appdata/nanobot/config.json |
