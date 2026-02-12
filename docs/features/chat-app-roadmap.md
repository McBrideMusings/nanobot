# Chat App Roadmap

**Date:** 2026-02-12
**Clients:** NanobotChat (SwiftUI, iOS/macOS) — primary; NanobotWeb (React) — validation/testing
**Current state:** MVP complete — text chat, history replay, connection management, debug logs

## Design Principles

- **Swift is the product, web is the test harness.** Both clients stay at rough parity, but Apple-exclusive features (LinkPresentation, APNs, Speech) don't need web equivalents.
- **Progressive disclosure.** Agent internals are visible but never overwhelming. One-line summaries, collapsible sections, full reader view.
- **Claude Code as UX reference.** Show the agent's work without drowning the user in it — compact tool call labels, expandable when you care, collapsible when you don't.
- **Streaming is opt-in.** Client-side toggle for streaming responses. Notifications only fire on final responses, never on chunks.

## Phases

1. [Agent Observability (Foundation)](./chat-app/phase-1-agent-observability.md) — event stream protocol, status bar, inline event cards, detail panel
2. [Core Chat Polish](./chat-app/phase-2-core-chat-polish.md) — streaming responses, markdown rendering, push notifications, link previews
3. [Rich Interactions](./chat-app/phase-3-rich-interactions.md) — replies, reactions, inline media, search
4. [Workspace & Intelligence](./chat-app/phase-4-workspace-intelligence.md) — workspace inspector, markdown editor, bot profile, notifications, voice
5. [Deferred / Research](./chat-app/phase-5-deferred-research.md) — sending media, bot avatar, token tracking, message regeneration
