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
| 2 | [Core Chat Polish](./chat-app/phase-2-core-chat-polish.md) | Streaming responses, markdown rendering, push notifications, link previews | Done |
| 3a | [Replies & Reactions](./chat-app/phase-3a-replies-and-reactions.md) | Swipe-to-reply, quoted previews, tapback reactions | Not started |
| 3b | [Inline Media](./chat-app/phase-3b-inline-media.md) | Render bot-provided images and video inline | Not started |
| 3c | [Chat Search](./chat-app/phase-3c-chat-search.md) | Client-side message search | Not started |
| 4a | [Workspace Inspector](./chat-app/phase-4a-workspace-inspector.md) | File browser, markdown viewer/editor | Not started |
| 4b | [Bot Profile](./chat-app/phase-4b-bot-profile.md) | Identity view, status, uptime, stats | Not started |
| 4c | [Notification Tuning](./chat-app/phase-4c-notification-tuning.md) | Per-event-type notification controls | Not started |
| 4d | [Voice Messages](./chat-app/phase-4d-voice-messages.md) | Voice notes with on-device transcription | Not started |
| 5 | [Deferred / Research](./chat-app/phase-5-deferred-research.md) | Sending media, bot avatar, token tracking, message regeneration | Not started |
