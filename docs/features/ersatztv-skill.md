# ErsatzTV Skill

**Status:** Implemented
**Effort:** Low (skill file only, no code changes)
**Impact:** AI-managed TV schedules via scripted schedules

## What Is ErsatzTV

ErsatzTV is an open-source platform that transforms a personal media library into live, custom TV channels with EPG (Electronic Program Guide) support. It creates IPTV streams from Plex/Jellyfin/Emby libraries.

## Focus: Scripted Schedules

The REST API for channel/schedule CRUD is UI-only. The real programmatic power is **scripted schedules** — Python scripts that ErsatzTV executes to dynamically build playouts. The skill focuses entirely on authoring and managing these scripts.

### What the Agent Can Do

- **Author playout scripts** — Write Python scripts that define content sources and build schedules
- **Edit existing scripts** — Modify scheduling logic, content rotation, time blocks
- **Manage content sources** — Collections, shows, searches, playlists, marathons
- **Day-parting** — Schedule different content for morning, prime time, late night
- **Commercial breaks** — Insert filler/bumper content between programs

## Implementation

### Skill Location

Custom workspace skill synced from the project-level `skills/` directory:

```
/root/projects/nanobot/skills/ersatztv/
  SKILL.md                          # Main skill file (~140 lines)
  references/
    scripted-api.md                 # Full API reference (~300 lines, loaded on demand)
```

Synced to the nanobot workspace via `sync-skills.sh` (called automatically by `run.sh`).

### Configuration Pattern

The skill has **hardcoded configuration** for Pierce's infrastructure (base URL, scripts directory) since it lives outside the upstream repo as a personal custom skill.

### Skill Frontmatter

```yaml
---
name: ersatztv
description: Author and manage ErsatzTV scripted schedule scripts for custom IPTV channel playouts.
metadata: {"nanobot":{"emoji":"📺","requires":{"bins":["curl"]}}}
---
```

## Script Structure

ErsatzTV calls scripts with 4 arguments (API host, build ID, build mode, custom args). Scripts implement three functions:

- `define_content()` — register content sources (collections, shows, searches, playlists)
- `reset_playout()` — set start time / initial state
- `build_playout()` — main loop that constructs the schedule

## API Categories

The scripted schedule API provides:

- **Content methods** — `add_collection`, `add_show`, `add_search`, `add_playlist`, `add_smart_collection`, `add_marathon`
- **Scheduling methods** — `add_count`, `add_duration`, `add_all`
- **Padding methods** — `pad_until`, `pad_to_next`, `pad_until_exact`
- **Control methods** — EPG grouping, graphics, watermarks, pre-roll, skip, wait
- **Query methods** — `context` (GET), `peek_next` (GET)

Full parameter schemas are in `references/scripted-api.md`.

## Heartbeat Integration

The agent can use heartbeat to periodically refresh channel schedules:

```markdown
- Check if ErsatzTV Saturday Morning Cartoons channel needs a content refresh (rotate monthly)
```
