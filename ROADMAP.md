# Roadmap

## Current State

Nanobot is a working personal AI assistant running in Docker on UnRAID. The core agent loop, tool system, memory, skills, and multi-channel support (WhatsApp bridge, web client, iOS client) are all functional. The web client has basic chat, agent observability, and navigation. The iOS client has basic chat. Key agent capabilities (MCP, improved heartbeat) and UI features (files, canvas, system monitor) are in progress.

## Milestones

### Core Agent (not started)
- MCP client support for external tool servers
- Configurable heartbeat with channel routing
- Memory search tool
- Background process tool

### Web Client — Foundation (not started)
- Connection management sheet
- Enhanced files tab with browser, editor, and context menus
- File links and @references in chat

### iOS — Foundation (not started)
- Native tab navigation (Chat, Canvas, Files, Logs)
- Enhanced files tab with SwiftUI NavigationStack
- Connection management sheet

### Content & Media (not started)
- Canvas tab for AI-generated HTML/SVG content (web + iOS)
- Inline image/video display in chat
- Client-side chat search

### Monitoring & Logs (not started)
- GPU/CPU system monitor with charts and process tables (web + iOS)
- Enhanced log viewer with split-pane layout (web + iOS)

### Social & Presence (not started)
- Swipe-to-reply and emoji reactions
- 3D animated robot avatar (web + iOS)
- Bot profile with dynamic status fields (web + iOS)

### Settings & Polish (not started)
- Settings sheets (web + iOS)
- Per-event-type notification controls
- Voice message input with on-device transcription
- iOS file links and @references
- Deferred research items (media sending, token/cost awareness, message regeneration)

### Media Skills (not started)
- Tautulli + Plex skill for analytics and home screen management
- Kometa skill for dynamic Plex collection management
