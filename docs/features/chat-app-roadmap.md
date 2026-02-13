# Chat App Roadmap

**Date:** 2026-02-12
**Clients:** NanobotChat (SwiftUI, iOS/macOS) — primary; NanobotWeb (React) — validation/testing
**Current state:** MVP complete — text chat, history replay, connection management, debug logs

## Design Principles

- **Swift is the product, web is the test harness.** Both clients stay at rough parity, but Apple-exclusive features (LinkPresentation, APNs, Speech) don't need web equivalents.
- **Progressive disclosure.** Agent internals are visible but never overwhelming. One-line summaries, collapsible sections, full reader view.
- **Claude Code as UX reference.** Show the agent's work without drowning the user in it — compact tool call labels, expandable when you care, collapsible when you don't.
- **Streaming is opt-in.** Client-side toggle for streaming responses. Notifications only fire on final responses, never on chunks.

## Progress

| Phase | Name | Key Deliverables | Status |
|-------|------|------------------|--------|
| 1 | [Agent Observability](./chat-app/phase-1-agent-observability.md) | Event stream protocol, status bar, inline event cards, detail panel | Done |
| 2 | [Core Chat Polish](./chat-app/phase-2-core-chat-polish.md) | Streaming responses, markdown rendering, push notifications, link previews | Not started |
| 3 | [Rich Interactions](./chat-app/phase-3-rich-interactions.md) | Replies, reactions, inline media, search | Not started |
| 4 | [Workspace & Intelligence](./chat-app/phase-4-workspace-intelligence.md) | Workspace inspector, markdown editor, bot profile, notifications, voice | Not started |
| 5 | [Deferred / Research](./chat-app/phase-5-deferred-research.md) | Sending media, bot avatar, token tracking, message regeneration | Not started |
