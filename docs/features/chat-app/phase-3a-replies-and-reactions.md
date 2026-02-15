# Phase 3a — Replies & Reactions

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
