# Getting Started

Nanobot is an ultra-lightweight personal AI assistant framework. It connects to LLM providers, exposes tools (file I/O, shell, web search), and communicates over chat channels.

## Requirements

- Python 3.11+
- An LLM provider API key (OpenRouter, Anthropic, OpenAI, etc.) or a local vLLM server
- Node.js 18+ (only if using WhatsApp)

## Install

**From source (recommended for development):**

```bash
git clone https://github.com/McBrideMusings/nanobot.git
cd nanobot
pip install -e .
```

**From PyPI:**

```bash
pip install nanobot-ai
```

## Configure

Initialize config and workspace:

```bash
nanobot onboard
```

Then edit `~/.nanobot/config.json`:

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    }
  }
}
```

For local models with vLLM:

```json
{
  "providers": {
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  }
}
```

## Chat

```bash
# One-shot message
nanobot agent -m "What is 2+2?"

# Interactive mode
nanobot agent

# Start gateway (enables channels + API)
nanobot gateway
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config and workspace |
| `nanobot agent -m "..."` | One-shot chat |
| `nanobot agent` | Interactive chat |
| `nanobot agent --no-markdown` | Plain-text output |
| `nanobot agent --logs` | Show runtime logs |
| `nanobot gateway` | Start gateway (channels + API) |
| `nanobot status` | Show provider status |
| `nanobot channels login` | Link WhatsApp (QR scan) |
| `nanobot channels status` | Show channel status |
| `nanobot cron add/list/remove` | Manage scheduled tasks |

## What's Next

- [Channels](/guide/channels) — Connect to Telegram, Discord, Slack, etc.
- [Skills](/guide/skills) — Extend the agent with custom skills
- [Providers](/guide/providers) — Configure LLM providers
- [Architecture](/architecture/overview) — How nanobot works internally
