# CLAUDE.md

## Project Overview

Nanobot is an ultra-lightweight personal AI assistant (~4,000 lines of core agent code). This repo contains:

- **`nanobot/`** — Python core agent (loop, tools, memory, skills, providers, channels)
- **`NanobotWeb/`** — React/TypeScript web client (Vite + TSX)
- **`NanobotChat/`** — SwiftUI iOS client
- **`bridge/`** — Node.js WhatsApp bridge
- **`docs/`** — VitePress documentation site + ticket board

## Ticket Workflow

Tickets live in `docs/tickets/*.md` with YAML frontmatter (`title`, `status`, `priority`, `tags`).

**When working on a ticket, always update it:**

1. **Starting work** — Change `status: backlog` → `status: doing` at the top of the ticket file
2. **During implementation** — Add notes, decisions, or scope changes to the ticket body as you go (e.g. under a `## Notes` section)
3. **Completing work** — Change `status: doing` → `status: done`
4. **If blocked or paused** — Leave status as `doing` and add a note explaining what's blocking

Valid board column keys: `backlog`, `doing`, `review`, `done` (must match `docs/board.md`).

This keeps the board view accurate and provides a record of decisions made during implementation.

## Key Paths

- Config schema: `nanobot/config/schema.py`
- Agent loop: `nanobot/agent/loop.py`
- Web app entry: `NanobotWeb/src/App.tsx`
- iOS app entry: `NanobotChat/NanobotChat/NanobotChatApp.swift`
- Tickets: `docs/tickets/*.md`
- UI prototype reference: `tmp/nanobot-prototype.jsx`

## Code Style

- Python: standard library conventions, type hints, minimal dependencies
- TypeScript/React: functional components, hooks, TSX
- SwiftUI: declarative views, `@State`/`@AppStorage` for state
- Keep it lean — nanobot's core value is being small and readable

## Common Commands

```bash
# Core agent
pip install -e .
nanobot agent -m "test"
nanobot gateway

# Web client
cd NanobotWeb && npm install && npm run dev

# Line count check
bash core_agent_lines.sh
```
