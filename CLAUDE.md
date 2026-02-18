# CLAUDE.md

## Project Overview

Nanobot is an ultra-lightweight personal AI assistant (~4,000 lines of core agent code). This repo contains:

- **`nanobot/`** — Python core agent (loop, tools, memory, skills, providers, channels)
- **`NanobotWeb/`** — React/TypeScript web client (Vite + TSX)
- **`NanobotChat/`** — SwiftUI iOS client
- **`bridge/`** — Node.js WhatsApp bridge
- **`docs/`** — VitePress documentation site + ticket board

## Workflow

This project uses GitHub Issues as the single source of truth for task tracking.

- All work happens on branches named `<type>/<short-slug>-<issue-number>` (e.g. `feat/mcp-support-3`)
- Commits follow conventional commit format: `<type>(<scope>): <summary> (#<issue-number>)`
- No PRs. Branches merge directly to main.
- Status is tracked via labels: `status:todo`, `status:in-progress`, `status:blocked`, `status:done`
- Milestones group issues by theme: Core Agent → Web Client Foundation → iOS Foundation → Content & Media → Monitoring & Logs → Social & Presence → Settings & Polish → Media Skills

### Session Start

1. Check current branch and whether it maps to an open issue.
2. Run `git log --oneline -10` and `gh issue list --state open` to understand current state.
3. If on a feature branch, continue that work. If on main, pick the next issue by milestone priority.
4. If `gh` commands fail with auth errors, stop and report. Do not attempt to fix auth.

### Session End

1. Close completed issues and update status labels.
2. Update ROADMAP.md if milestone progress has changed.
3. Update README.md if completed work changes how the project is used, installed, or configured.

### References

- See ROADMAP.md for high-level project direction and milestone status.
- See GitHub Issues for individual work items: https://github.com/McBrideMusings/nanobot/issues
- `docs/tickets/` — legacy ticket files, superseded by GitHub Issues (do not add new tickets here)

## Key Paths

- Config schema: `nanobot/config/schema.py`
- Agent loop: `nanobot/agent/loop.py`
- Web app entry: `NanobotWeb/src/App.tsx`
- iOS app entry: `NanobotChat/NanobotChat/NanobotChatApp.swift`
- Tickets: GitHub Issues (https://github.com/McBrideMusings/nanobot/issues)
- UI prototype reference: `tmp/nanobot-prototype.jsx`

## Runtime Environment

Nanobot runs inside a Docker container on UnRAID. Use `run.sh` to build and deploy.

- **To run CLI commands against the live instance:** `docker exec nanobot <command>`
- Example: `docker exec nanobot nanobot heartbeat trigger`
- Do NOT run `nanobot` commands directly on the host — there's no API key configured outside the container.
- Config lives at `/mnt/user/appdata/nanobot/config.json` on the host, mounted as `/root/.nanobot/config.json` in the container.

## Commit Rules

- NEVER add "Co-Authored-By" lines to commits. No AI attribution. Ever.

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
