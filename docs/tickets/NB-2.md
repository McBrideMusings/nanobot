<!-- Migrated to GitHub Issues on 2026-02-17. See https://github.com/McBrideMusings/nanobot/issues/29 -->
---
title: Phase 5 — Deferred Research
status: backlog
priority: low
tags:
  - chat-app
  - research
id: 2
---

# Phase 5 — Deferred / Research

No implementation commitment. Tracked for future consideration.

## Sending Media

Photo picker, file upload, include in message. Requires:

- HTTP upload endpoint on the backend (binary over WebSocket is impractical).
- LLM provider must accept images (multimodal model support).
- Depends on upstream multimodal work.

## Bot Avatar Rendering

Research options for giving the bot a dynamic visual identity:

- **Lottie / SwiftUI animation:** Vector-animated character that reacts to agent state. Eyes track activity, expression shifts. Needs design work.
- **3D model + ARKit blend shapes:** 52 facial expression parameters driven by agent state/sentiment. Closest to a programmable Memoji. Needs a 3D model.
- **Generated static expression set:** Pre-made avatar images for different states (thinking, happy, working, idle). Simplest option.
- **Note:** Apple does not expose a public API for programmatic Memoji creation or control.

## Token / Cost Awareness

`LLMResponse` already includes `usage` data. Could surface:

- Per-message token count (subtle label on each bot message).
- Aggregate usage view (daily/weekly token and cost tracking).

## Message Regeneration

"Retry" button on bot responses to get a different answer. Protocol addition: `{"type": "regenerate", "message_id": "..."}`.
