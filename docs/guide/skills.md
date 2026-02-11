# Skills

Skills are markdown-based extensions that teach the agent new capabilities. They're loaded into the system prompt so the agent knows how to use them.

## Skill Format

Each skill is a directory with a `SKILL.md` file containing YAML frontmatter and markdown instructions:

```
skills/
  my-skill/
    SKILL.md
```

Example `SKILL.md`:

```yaml
---
name: my-skill
description: "Does something useful"
metadata:
  nanobot:
    emoji: "🔧"
    requires:
      bins: ["some-cli"]
    always: false
---

# My Skill

Instructions for the agent on how to use this skill...
```

## Skill Locations

| Location | Type |
|----------|------|
| `nanobot/skills/` | Built-in (shipped with nanobot) |
| `~/.nanobot/workspace/skills/` | User-defined (your custom skills) |

## Built-in Skills

| Skill | Description |
|-------|-------------|
| **github** | Interact with GitHub via `gh` CLI |
| **weather** | Get weather information |
| **tmux** | Manage tmux sessions |
| **cron** | Manage scheduled tasks |
| **summarize** | Summarize content |
| **skill-creator** | Create new skills |

## Progressive Loading

Skills marked `always: true` are loaded fully into the system prompt every time. Other skills are summarized — the agent sees a one-line description and can read the full skill via `read_file` when needed.

This minimizes token usage while keeping all capabilities discoverable.

## Frontmatter Options

| Field | Description |
|-------|-------------|
| `name` | Skill identifier |
| `description` | One-line summary (shown in skill listing) |
| `metadata.nanobot.emoji` | Display emoji |
| `metadata.nanobot.requires.bins` | Required CLI tools |
| `metadata.nanobot.requires.env` | Required environment variables |
| `metadata.nanobot.install` | Install instructions for missing deps |
| `metadata.nanobot.always` | Load full content into every prompt |

## Creating a Skill

The easiest way is to ask the agent itself (it has a `skill-creator` skill), or manually:

1. Create `~/.nanobot/workspace/skills/my-skill/SKILL.md`
2. Add YAML frontmatter with name, description, requirements
3. Write markdown instructions for the agent
4. Restart the gateway — the skill is auto-discovered

## Planned Skills

See the [Features](/features/ersatztv-skill) section for planned skills:
- [ErsatzTV](/features/ersatztv-skill) — TV channel and schedule management
- [Tautulli + Plex](/features/tautulli-plex-skill) — Plex analytics and home screen control
- [Kometa](/features/kometa-skill) — Plex collection authoring
