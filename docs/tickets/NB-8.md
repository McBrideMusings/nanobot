<!-- Migrated to GitHub Issues on 2026-02-17. See https://github.com/McBrideMusings/nanobot/issues/30 -->
---
title: Tautulli + Plex Skill
status: backlog
priority: medium
tags:
  - skill
id: 8
---

# Tautulli + Plex Skill

**Priority:** Medium
**Effort:** Low (skill file only, no code changes)
**Impact:** AI-driven Plex analytics and home screen management

## What This Enables

Combining Tautulli (analytics) with the Plex API (control), the agent can:
- **Report on viewing habits** - What's being watched, by whom, how often
- **Manage the home screen** - Pin/unpin collections, reorder hubs, feature content
- **Surface insights** - "You haven't watched anything from your documentary collection in 3 months"
- **Monitor activity** - Current streams, bandwidth usage, transcoding load
- **Curate recommendations** - Based on watch history patterns

## Tautulli API

Tautulli has a comprehensive REST API with 60+ commands.

### Connection

```
http://{host}:{port}/api/v2?apikey={api_key}&cmd={command}
```

### Key Commands

**Activity & Monitoring:**
- `get_activity` - Current streams with session details
- `server_status` - Plex server connection status
- `terminate_session` - Kill a stream

**Analytics & Stats:**
- `get_home_stats` - Top movies, shows, users, platforms
- `get_plays_by_date` - Play trends over time
- `get_plays_by_hourofday` - Hourly viewing patterns
- `get_plays_per_month` - Monthly trends
- `get_plays_by_top_10_users` - User rankings
- `get_plays_by_top_10_platforms` - Platform rankings
- `get_plays_by_stream_type` - Direct play vs transcode

**Library:**
- `get_libraries` - All library sections with counts
- `get_library_watch_time_stats` - Watch time per library
- `get_library_media_info` - File details (codecs, resolution, bitrate)
- `get_recently_added` - New content

**Users:**
- `get_users` - All users with permissions
- `get_user_watch_time_stats` - Per-user watch time
- `get_user_player_stats` - What devices a user uses

**History:**
- `get_history` - Full play history with filters
- `get_metadata` - Detailed media info (cast, genres, file info)

## Plex API

The Plex Media Server API allows direct control of the server.

### Connection

```
http://{host}:32400/{endpoint}?X-Plex-Token={token}
```

### Key Endpoints

**Libraries:**
- `GET /library/sections` - List libraries
- `GET /library/sections/{id}/all` - All items in a library
- `GET /library/sections/{id}/collections` - Collections in a library
- `GET /library/metadata/{ratingKey}` - Item details

**Home Screen / Hubs:**
- `GET /hubs` - Home screen hubs
- `GET /hubs/sections/{id}` - Library-specific hubs
- `PUT /hubs/sections/{id}/manage` - Manage pinned hubs
- `POST /hubs/sections/{id}/manage` - Add managed hub

**Collections:**
- `GET /library/sections/{id}/collections` - List collections
- `PUT /library/collections/{id}` - Update collection
- `POST /library/collections` - Create collection

**Playlists:**
- `GET /playlists` - List playlists
- `POST /playlists` - Create playlist

## Skill File

`~/.nanobot/workspace/skills/tautulli-plex/SKILL.md`:

```yaml
---
name: tautulli-plex
description: "Plex analytics via Tautulli and Plex server management"
metadata:
  nanobot:
    emoji: "🎬"
    always: false
---
```

## Common Tasks

### Weekly Viewing Report
1. Call `get_home_stats` with `time_range=7`
2. Call `get_plays_by_date` for the past week
3. Summarize: top content, total watch time, most active users

### Home Screen Management
1. Get current hubs: `GET /hubs`
2. Identify collections to feature
3. Pin/unpin collections using the manage endpoint
4. Confirm changes

### Activity Check
1. Call `get_activity` to see current streams
2. Report who's watching what, stream quality, transcode status

## Guidelines

- Read-only operations are always safe
- Confirm before modifying home screen, terminating streams, or changing collections
- When reporting stats, be concise - highlight interesting patterns, don't dump raw data
- Store API keys in memory/MEMORY.md after first setup (not in the skill file)

## Open Questions

- What are the exact Tautulli and Plex host:port values?
- Tautulli API key (found in Tautulli Settings > Web Interface > API Key)
- Plex token (found in Plex account settings or via XML trick)
- Which Plex libraries exist? (Movies, TV, Music, etc.)
