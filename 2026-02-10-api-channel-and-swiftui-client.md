# API Channel + SwiftUI Client

## Problem

All existing nanobot connectors (Telegram, Discord, WhatsApp, etc.) expose a publicly-discoverable identifier that anyone on the internet can message. The only defense is an application-level `allowFrom` whitelist in Python. This is a threat vector for a personal home assistant -- if the whitelist fails, the system is exposed to the public internet.

## Solution

Replace the third-party connector with two new components:

1. **ApiChannel** -- a WebSocket server channel in nanobot, bound to the Tailscale interface only
2. **NanobotChat** -- a SwiftUI app (iOS/iPadOS/macOS) that connects over Tailscale

Network-level security: if you can reach the port, you're on the Tailscale network, you're authorized. No application-level auth needed.

## Architecture

```
SwiftUI App (iPhone/iPad/Mac)
    |
    | WebSocket over Tailscale
    |
    v
ApiChannel (nanobot, bound to Tailscale IP)
    |
    | MessageBus (InboundMessage / OutboundMessage)
    |
    v
AgentLoop (existing nanobot core)
```

## Wire Protocol

JSON over WebSocket. Deliberately minimal.

### MVP Messages

Client -> Server:
```json
{"type": "message", "content": "hello"}
```

Server -> Client:
```json
{"type": "response", "content": "Hi! How can I help?", "id": "msg_abc123"}
```

### Reserved for Future Streaming

These types do NOT need to be implemented in the MVP. The SwiftUI client should ignore unknown message types, so these can be added later without breaking anything.

```json
{"type": "stream_start", "id": "msg_abc123"}
{"type": "stream_chunk", "id": "msg_abc123", "delta": "Hi! "}
{"type": "stream_end", "id": "msg_abc123"}
```

## Implementation Plan

### Step 1: ApiChannel (Python, in nanobot repo)

**Branch:** `pierce`
**Files to create/modify:**

#### 1a. Create `nanobot/channels/api.py` (~100-150 lines)

New channel implementation following the existing pattern (see `telegram.py`, `slack.py` for reference).

- Subclass `BaseChannel`
- `start()`: launch an `aiohttp` or `websockets` WebSocket server on configured host:port
- `stop()`: shut down the server
- `send(msg: OutboundMessage)`: forward response JSON to the connected WebSocket client(s)
- On incoming WebSocket message: parse JSON, call `self._handle_message()` to push to the MessageBus
- Track connected clients by a simple connection ID (use as both `sender_id` and `chat_id`)

Dependencies to evaluate:
- `websockets` library (lightweight, async-native, no extra framework) -- preferred
- `aiohttp` (heavier, but already may be a transitive dependency)

Check what's already in the dependency tree before adding anything new.

#### 1b. Add `ApiConfig` to `nanobot/config/schema.py`

```python
class ApiConfig(BaseModel):
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 18790
```

Add to `ChannelsConfig`:
```python
api: ApiConfig = Field(default_factory=ApiConfig)
```

#### 1c. Register in `nanobot/channels/manager.py`

Add the `api` channel initialization block following the existing pattern:
```python
if self.config.channels.api.enabled:
    from nanobot.channels.api import ApiChannel
    self.channels["api"] = ApiChannel(self.config.channels.api, self.bus)
```

#### 1d. Update `config.sample.json`

Add `api` channel example:
```json
"channels": {
    "api": {
        "enabled": true,
        "host": "100.x.x.x",
        "port": 18790
    }
}
```

#### 1e. Update Docker run command

The existing `nanobot.sh` already binds port 18790 to the Tailscale IP (`-p 100.114.249.118:18790:18790`). This should work as-is. Verify the ApiChannel inside the container listens on `0.0.0.0:18790` so Docker's port mapping reaches it.

### Step 2: SwiftUI App (NanobotChat)

**Location:** `/root/projects/nanobot/NanobotChat/` (sibling to `repo/`)

This is a new Xcode project. It will NOT live inside the nanobot repo -- it's a separate codebase that happens to share the parent directory (and thus the parent-level CLAUDE.md).

#### 2a. Project structure

```
NanobotChat/
  NanobotChat.xcodeproj
  NanobotChat/
    NanobotChatApp.swift       -- App entry point
    ContentView.swift           -- Main chat view
    WebSocketClient.swift       -- WebSocket connection manager
    Message.swift               -- Chat message model
    Settings.swift              -- Server URL configuration
```

#### 2b. WebSocketClient

- Uses `URLSessionWebSocketTask` (built-in, no dependencies)
- Connects to `ws://<tailscale-ip>:<port>`
- Sends `{"type": "message", "content": "..."}`
- Receives and parses response JSON
- Handles reconnection on disconnect
- Published properties for SwiftUI binding: `isConnected`, `messages`

#### 2c. ContentView (Chat UI)

- `ScrollView` with `LazyVStack` of message bubbles
- Distinguish sent vs received messages (left/right alignment or color)
- `TextField` + send button at bottom
- Auto-scroll to newest message
- Connection status indicator (green dot / red dot)

#### 2d. Settings

- Hardcode the Tailscale IP + port for MVP
- Store in `@AppStorage` so it persists and can be changed later
- Optional: a simple settings sheet to update the server URL

#### 2e. Platform targets

- Single SwiftUI target
- Deploy to iOS 17+, macOS 14+ (these share the same SwiftUI APIs for what we need)
- No iPad-specific layout needed for MVP -- iPhone layout works fine on iPad

### Step 3: Integration Testing

1. Start nanobot gateway with `api` channel enabled
2. Open SwiftUI app, verify WebSocket connects
3. Send a message, verify it reaches the agent and response comes back
4. Kill the server, verify the app shows disconnected state
5. Restart the server, verify reconnection

### Step 4: Docker/Deployment Updates

- Verify `nanobot.sh` works with the new channel config
- Update `config.sample.json` at the parent level to include `api` channel
- Disable Telegram channel in config (or leave it, but it's no longer the primary interface)

## What This Does NOT Include (YAGNI)

- No streaming (reserved in protocol but not implemented)
- No authentication (Tailscale IS the auth)
- No message persistence on the client (nanobot already persists sessions server-side)
- No push notifications (app is open when you're using it)
- No file/image upload from the client (text only for MVP)
- No multiple chat threads (single conversation)
- No user accounts or multi-user support

## Open Questions

1. **WebSocket library for Python side:** `websockets` (preferred, minimal) vs `aiohttp` -- check nanobot's existing dependency tree
2. **Xcode project creation:** Will need to be done on a Mac. The plan can be written and the Swift source files drafted here, but the `.xcodeproj` needs Xcode. Alternatively, use Swift Package Manager with a `Package.swift` for the app target.

## File Layout After Implementation

```
/root/projects/nanobot/
  CLAUDE.md                     -- project-wide guidance
  config.sample.json            -- config template (updated with api channel)
  nanobot.sh                    -- build & run
  nanobot-logs.sh               -- view logs
  docs/plans/                   -- design documents
  repo/                         -- nanobot upstream (branch: pierce)
    nanobot/channels/api.py     -- NEW: WebSocket API channel
    nanobot/config/schema.py    -- MODIFIED: add ApiConfig
    nanobot/channels/manager.py -- MODIFIED: register api channel
  NanobotChat/                  -- NEW: SwiftUI app
    NanobotChat/
      NanobotChatApp.swift
      ContentView.swift
      WebSocketClient.swift
      Message.swift
      Settings.swift
```
