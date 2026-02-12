# Phase 4 — Workspace & Intelligence

**Scope:** New views + backend endpoints

## Workspace Inspector

Browse the bot's workspace files (markdown files, memory, daily notes, HEARTBEAT.md, etc.).

- File browser view showing workspace structure.
- Tap a file to view with rendered markdown.
- Edit button switches to a built-in markdown editor.
- Save writes changes back to the workspace.
- Shares the markdown rendering component from Phase 2.

## Built-in Markdown Editor

A reusable editing component for markdown files. Used by the workspace inspector and potentially other views. Supports:

- Syntax-aware text editing.
- Preview toggle (edit / rendered view).
- Save/cancel actions.

## Bot Profile View

A dedicated view for the bot's identity, accessible by tapping the bot's avatar/name in the chat header.

- **Name and description** — pulled from `IDENTITY.md` or `SOUL.md` in the workspace.
- **Current status** — idle, working, sleeping (driven by agent state).
- **Uptime** — how long the agent has been running.
- **Stats** — messages exchanged, tasks completed, heartbeats run.

## Notification Tuning

Granular per-event-type controls:

- Direct responses: always (non-configurable baseline).
- Heartbeat results: only when action was taken (not `HEARTBEAT_OK`).
- Sub-agent completions: optional.
- Cron job failures: optional (successes silent by default).

## Voice Messages

Send voice notes that are transcribed client-side before sending as text.

- **Apple:** Use the Speech framework for on-device transcription.
- **Before building:** Check upstream nanobot development for multimodal/voice support that could be merged in to reduce effort.
- Bot responds with text (no voice synthesis in scope for now).
