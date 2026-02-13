# Architecture Overview

Nanobot is built around a message bus that routes messages between channels and an agent loop. The entire core is ~4,000 lines of Python.

## High-Level Flow

```
Channel (Telegram, Slack, API, ...)
    ↓ InboundMessage
Message Bus
    ↓
Agent Loop
    ↓ builds context
Context Builder (system prompt + memory + skills + history)
    ↓
LLM Provider (via LiteLLM)
    ↓ response with tool calls
Tool Registry → execute tools → loop back to LLM
    ↓ final response
Message Bus
    ↓ OutboundMessage
Channel → User
```

## Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **AgentLoop** | `agent/loop.py` | Message → LLM → tools → response |
| **ContextBuilder** | `agent/context.py` | Assembles system prompts |
| **ToolRegistry** | `agent/tools/registry.py` | Tool management and execution |
| **SkillsLoader** | `agent/skills.py` | Loads skills from workspace |
| **SessionManager** | `session/manager.py` | Conversation history per channel:chat_id |
| **MessageBus** | `bus/queue.py` | Event routing between components |
| **ProvidersRegistry** | `providers/registry.py` | LLM provider configuration |
| **ChannelManager** | `channels/manager.py` | Channel lifecycle |
| **SubagentManager** | `agent/subagent.py` | Background task execution |
| **CronService** | `cron/service.py` | Scheduled task execution |
| **HeartbeatService** | `heartbeat/service.py` | Periodic agent wake-up |

## Module Layout

```
nanobot/
├── agent/          # Core agent logic
│   ├── loop.py     # Agent loop (LLM ↔ tool execution)
│   ├── context.py  # System prompt builder
│   ├── memory.py   # Memory read/write
│   ├── skills.py   # Skills loader
│   ├── subagent.py # Background tasks
│   └── tools/      # Built-in tools
├── channels/       # Chat integrations
├── bus/            # Message routing
├── cron/           # Scheduled tasks
├── heartbeat/      # Proactive wake-up
├── providers/      # LLM providers
├── session/        # Conversation state
├── config/         # Configuration schema
└── cli/            # CLI commands
```

## Key Design Decisions

**Workspace-centric state.** All agent state lives in `~/.nanobot/workspace/` — memory, sessions, skills, bootstrap files. No scattered config files.

**Progressive skill loading.** Always-loaded skills get full content in the system prompt. Others get one-line summaries. The agent reads full content on demand via `read_file`.

**Provider registry.** Single source of truth for all LLM providers. Auto-detection, auto-prefixing, auto-discovery of model capabilities (name, context window), no if-elif chains.

**Line count discipline.** ~4,000 lines of core code. Avoid abstractions unless they remove more code than they add.

See [Agent Loop](/architecture/agent-loop) and [Workspace](/architecture/workspace) for deeper dives.
