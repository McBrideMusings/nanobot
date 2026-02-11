# Kometa Skill

**Priority:** Medium
**Effort:** Low (skill file only, no code changes)
**Impact:** AI-authored Plex collections via Kometa YAML configs

## What Is Kometa

Kometa (formerly Plex Meta Manager) is a Python tool that automatically builds and maintains Plex collections, overlays, and playlists. It's configured via YAML files that define collection rules using "builders" - sources like IMDb, TMDb, Trakt, Plex smart filters, Tautulli, and 15+ others.

Pierce uses Kometa primarily to construct Plex collections (and potentially ErsatzTV collections). The agent's role is authoring and managing these YAML config files.

## What the Skill Enables

The agent can:
- **Author collection configs** - Write Kometa YAML for new collections
- **Look up IDs** - Find IMDb/TMDb IDs for movies, shows, actors, directors
- **Use smart filters** - Create dynamic Plex collections that auto-update
- **Combine builders** - Mix IMDb charts, TMDb lists, Trakt trending, etc.
- **Manage overlays** - Add rating badges, resolution tags, etc. to posters
- **Review existing configs** - Read and explain current Kometa YAML

## Kometa Builder Sources

Kometa supports 18 builder types:

| Builder | Source | Example Use |
|---------|--------|-------------|
| **plex** | Local Plex metadata | Smart filters, search |
| **tmdb** | TheMovieDB | Collections, lists, trending, popular |
| **trakt** | Trakt.tv | Lists, charts, recommendations |
| **imdb** | IMDb | Charts (Top 250), lists, search, awards |
| **mdblist** | MDBList.com | Curated lists |
| **tvdb** | TheTVDB | Shows, movies, lists |
| **boxofficemojo** | Box Office Mojo | Box office charts |
| **tautulli** | Tautulli | Most watched, most popular |
| **radarr** | Radarr | Movies by tag |
| **sonarr** | Sonarr | Shows by tag |
| **letterboxd** | Letterboxd | Movie lists |
| **anidb/anilist/mal** | Anime DBs | Anime collections |

## YAML Config Format

### Basic Collection

```yaml
collections:
  Best of 2025:
    tmdb_year:
      year: 2025
      limit: 50
    sort_title: "!020_Best of 2025"
    summary: "Top rated films from 2025"
```

### Smart Filter (Dynamic, Auto-Updates)

```yaml
collections:
  4K HDR Movies:
    smart_filter:
      all:
        resolution: 4K
        hdr: true
      sort_by: added.desc
      limit: 100
```

### Multi-Builder Collection

```yaml
collections:
  Pierce's Watchlist:
    trakt_watchlist:
      username: pierce
      sort_by: rank
    imdb_search:
      type: movie
      list: ls123456789
    sync_mode: sync
    collection_order: custom
```

### IMDb/TMDb Lookups

```yaml
collections:
  Christopher Nolan:
    tmdb_person: 525
    sort_title: "!030_Nolan"
    summary: "Films directed by Christopher Nolan"

  IMDb Top 250:
    imdb_chart: top_movies
    collection_order: custom
    sync_mode: sync
```

### Overlays

```yaml
overlays:
  Resolution:
    overlay:
      name: resolution
    plex_search:
      all:
        resolution: 4K
```

## ID Lookup Strategy

The agent needs to look up IDs (IMDb, TMDb) when authoring configs. Methods:

1. **TMDb API** - `web_fetch("https://api.themoviedb.org/3/search/movie?query=inception&api_key=KEY")`
2. **IMDb search** - `web_fetch("https://www.imdb.com/find/?q=inception")` and parse results
3. **web_search** - Search for "inception 2010 imdb id" or "christopher nolan tmdb id"

For TMDb API access, a free API key is available at themoviedb.org.

## Skill File

`~/.nanobot/workspace/skills/kometa/SKILL.md`:

```yaml
---
name: kometa
description: "Author and manage Kometa YAML configs for Plex collections"
metadata:
  nanobot:
    emoji: "🎨"
    always: false
---
```

```markdown
# Kometa Collection Management

You can author and manage Kometa YAML configuration files for Plex collections.

## Kometa Config Location

Kometa configs are stored at: /mnt/user/appdata/kometa/config/ (update if different)

Key files:
- `config.yml` - Main Kometa config
- `collections/` or individual library YAML files - Collection definitions

Use `read_file` and `write_file` to manage these configs.

## Writing Collections

### YAML Format

```yaml
collections:
  Collection Name:
    # One or more builders (sources)
    builder_type: builder_value
    # Optional metadata
    summary: "Description"
    sort_title: "!010_Collection Name"  # ! prefix for sort order
    collection_order: custom            # or release, alpha, etc.
    sync_mode: sync                     # sync (match exactly) or append
```

### Common Builders

**By person (TMDb ID required):**
```yaml
  Director Collection:
    tmdb_person: 525          # Christopher Nolan
```

**By IMDb chart:**
```yaml
  Top 250:
    imdb_chart: top_movies
```

**By smart filter (dynamic, no re-run needed):**
```yaml
  Recently Added 4K:
    smart_filter:
      all:
        resolution: 4K
      sort_by: added.desc
      limit: 50
```

**By search:**
```yaml
  90s Action:
    plex_search:
      all:
        genre: Action
        decade: 1990
```

### Looking Up IDs

When you need TMDb or IMDb IDs:
1. Search TMDb: `web_fetch("https://api.themoviedb.org/3/search/movie?query=NAME&api_key=KEY")`
2. Or use web_search: `web_search("christopher nolan tmdb person id")`
3. IMDb IDs look like: tt1234567 (titles), nm1234567 (people)
4. TMDb IDs are plain numbers

Store frequently used IDs in memory for reuse.

## Smart Filter Reference

Smart filters create dynamic collections that auto-update without re-running Kometa.

**Base:** Must start with `any` (OR) or `all` (AND)

**Filter types:**
- Boolean: `hdr`, `unmatched`, `duplicate`, `unplayed`
- Date: `added`, `release`, `last_played` (modifiers: `.before`, `.after`)
- Number: `year`, `plays`, `audience_rating` (modifiers: `.gt`, `.lt`, `.gte`, `.lte`)
- String: `title`, `studio` (modifiers: `.is`, `.not`, `.begins`, `.ends`)
- Tag: `genre`, `actor`, `director`, `resolution`, `network`, `country`

## Guidelines

- Always read existing config files before modifying
- Validate YAML syntax before writing
- Use `sort_title` with `!` prefix and numbers for custom ordering
- Prefer smart filters when possible (they auto-update)
- Confirm collection changes with Pierce before writing
- After writing configs, remind Pierce to run Kometa to apply changes
```

## Open Questions

- Where are Kometa configs stored on Pierce's UnRAID? (assumed /mnt/user/appdata/kometa/config/)
- Does Pierce have a TMDb API key configured?
- Which Plex libraries should Kometa manage? (Movies, TV, Anime, etc.)
- Is Kometa run on a schedule (cron) or manually?
