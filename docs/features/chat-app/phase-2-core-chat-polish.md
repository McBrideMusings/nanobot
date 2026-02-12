# Phase 2 — Core Chat Polish

**Scope:** Mostly client-side

## Streaming Responses

Uses the already-reserved `stream_start` / `stream_chunk` / `stream_end` protocol types. Text appears word-by-word as the bot generates it.

- Client-side toggle to enable/disable streaming display.
- When streaming is off, the user sees the agent status bar activity (from Phase 1), then the final message.
- Notifications only fire on the final complete response, never on individual chunks.

## Markdown Rendering

Render bot responses as rich text — code blocks with syntax highlighting, lists, bold/italic, inline code, links. The current `Text()` view in `MessageBubbleView` gets replaced with a markdown renderer.

Shared component: the markdown renderer built here is reused in the workspace inspector (Phase 4).

## Push Notifications (APNs)

Must work when the app is closed. Requires:

- APNs registration and device token management on the client.
- Backend endpoint or mechanism to send push notifications via APNs.
- Baseline trigger: all direct bot responses.
- Other event types (heartbeats, sub-agent completions, cron) are configurable (see Phase 4 notification tuning).

## Link Previews

Detect URLs in message content and render preview cards (title, image, favicon) below the message bubble.

- **Swift:** `LPMetadataProvider` from LinkPresentation framework — entirely client-side, no backend work.
- **Web:** Open Graph meta tag fetching (may need a backend proxy for CORS).

Quick win with high polish impact.
