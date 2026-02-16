---
layout: page
board: true
ticketsDir: tickets
ticketPrefix: NB
defaultColumn: backlog
columns:
  - { key: backlog, label: Backlog, color: "#718096" }
  - { key: doing, label: In Progress, color: "#e6a817" }
  - { key: review, label: Review, color: "#9f7aea" }
  - { key: done, label: Done, color: "#6bcb6b" }
---

# Project Board

**Clients:** NanobotChat (SwiftUI, iOS/macOS) — primary; NanobotWeb (React) — validation/testing
**Current state:** MVP complete — text chat, history replay, connection management, debug logs

## Design Principles

- **Swift is the product, web is the test harness.** Both clients stay at rough parity, but Apple-exclusive features (LinkPresentation, APNs, Speech) don't need web equivalents.
- **Progressive disclosure.** Agent internals are visible but never overwhelming. One-line summaries, collapsible sections, full reader view.
- **Claude Code as UX reference.** Show the agent's work without drowning the user in it — compact tool call labels, expandable when you care, collapsible when you don't.
- **Streaming is opt-in.** Client-side toggle for streaming responses. Notifications only fire on final responses, never on chunks.
