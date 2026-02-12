# Phase 3 — Rich Interactions

**Scope:** Protocol extensions + client UI

## Reply to Specific Messages

- Swipe-to-reply gesture (like iMessage).
- Shows quoted preview of the original message above the reply.
- Protocol: add optional `reply_to` field to outgoing messages.
- The bot can also reply to specific user messages when contextually relevant.

## Emoji Reactions

- Tap-and-hold a message to add a tapback reaction (like iMessage).
- Protocol: `{"type": "reaction", "message_id": "...", "emoji": "👍"}`.
- Reactions persist across reconnects (requires backend storage).
- The bot can react to user messages as a lightweight acknowledgment.

## Receiving Media Inline

Render images and video inline in chat when the bot includes media URLs. The `OutboundMessage.media` field already exists but is unused.

- Images: thumbnail in the bubble, tap to view full-size.
- Video: inline player with playback controls.
- No upload pipeline needed — this is display-only for bot-provided URLs.

## Chat Search

Search bar that filters messages by content.

- **Phase 3:** Client-side search over loaded message history.
- **Future:** Server-side search endpoint if conversation history grows too large for client-side filtering.
