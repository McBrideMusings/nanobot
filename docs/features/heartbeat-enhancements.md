# Heartbeat Enhancements

**Priority:** High
**Effort:** Low-Medium (~50-100 lines of changes)
**Impact:** Makes heartbeat actually useful by routing results to channels

## Current State

The heartbeat service exists and works:
- Reads `HEARTBEAT.md` every 30 minutes
- Sends the content to the agent for processing
- Agent executes tasks and responds

**What's missing:**
- Heartbeat responses don't go anywhere visible - they're processed internally but the agent has no channel context during heartbeat, so `message` tool calls may fail or go nowhere
- No way to configure which channel receives heartbeat notifications
- No way to adjust the interval without code changes
- The heartbeat prompt is generic ("read HEARTBEAT.md") rather than giving the agent useful context

## Proposed Changes

### 1. Route Heartbeat Responses to a Channel

The most important change. When the heartbeat fires and the agent has something to report, it should be able to notify you.

```json
{
  "heartbeat": {
    "enabled": true,
    "intervalMinutes": 30,
    "channel": "api",
    "chatId": "default"
  }
}
```

**Implementation:** When processing a heartbeat, set the agent's channel context to the configured channel/chatId. This way when the agent calls `message()` during heartbeat processing, it goes to the right place. If the agent's final response isn't "HEARTBEAT_OK", also send the response to the configured channel.

### 2. Make Interval Configurable

Currently hardcoded to 30 minutes. Add to config:

```json
{
  "heartbeat": {
    "intervalMinutes": 30
  }
}
```

Simple change in `HeartbeatService.__init__()` to read from config.

### 3. Improve the Heartbeat Prompt

Current prompt:
> "Read HEARTBEAT.md in your workspace. Follow any instructions or tasks listed there. If nothing needs attention, reply with just: HEARTBEAT_OK"

Better prompt that gives the agent context:
> "This is a scheduled heartbeat check. Read HEARTBEAT.md and execute any tasks listed there. You can use all your tools. If you need to notify Pierce, use the message tool. Current time: {timestamp}. If nothing needs attention, reply: HEARTBEAT_OK"

### 4. Heartbeat Config Schema

```python
class HeartbeatConfig(BaseModel):
    enabled: bool = True
    interval_minutes: int = 30
    channel: str = ""      # Empty = don't route responses
    chat_id: str = ""
```

Add to main config alongside existing gateway/channels/tools sections.

## Files to Change

- `nanobot/config/schema.py` - Add `HeartbeatConfig`
- `nanobot/heartbeat/service.py` - Read config, improve prompt, add channel context
- `nanobot/gateway/server.py` (or wherever heartbeat is initialized) - Pass config to HeartbeatService

## Pierce's HEARTBEAT.md

Your current heartbeat file is already well-designed:

```markdown
## What to do on heartbeat
Browse the internet for interesting stuff:
- Tech news, science discoveries, weird corners of the web
...

## When to reach out
Only send a DM to me if:
- Something is genuinely interesting, surprising, or useful
...
```

This will work great once heartbeat responses are routed to a channel. The agent will browse the web every 30 minutes and DM you when it finds something worth sharing.

## Testing

- Verify heartbeat fires at configured interval
- Verify agent response is routed to configured channel
- Verify HEARTBEAT_OK responses are suppressed (not sent to channel)
- Verify heartbeat works with empty/missing config (backwards compatible)
