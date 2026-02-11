# Code Style

## Linting

Nanobot uses **ruff** for linting:

```bash
ruff check nanobot/
```

Configuration from `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]
```

Rules enabled: errors (E), pyflakes (F), isort (I), naming (N), warnings (W). Line length warnings (E501) are ignored.

## Conventions

- **Type hints** encouraged but not required
- **Docstrings** at module and class level; function-level optional
- **Functions** should be small and focused
- **Line count discipline** — core agent is ~4,000 lines. Avoid abstractions unless they remove more code than they add.

## Adding New Features

**New Tool:**
1. Create `nanobot/agent/tools/my_tool.py` extending `Tool`
2. Implement `name`, `description`, `parameters` (JSON schema), `execute()`
3. Register in `AgentLoop._register_default_tools()`

**New Provider:**
1. Add `ProviderSpec` to `PROVIDERS` in `nanobot/providers/registry.py`
2. Add field to `ProvidersConfig` in `nanobot/config/schema.py`

**New Channel:**
1. Create `nanobot/channels/my_channel.py` extending `Channel`
2. Implement `start()`, `stop()`, message handling
3. Add config to `nanobot/config/schema.py`
4. Register in `nanobot/channels/manager.py`

**New Skill:**
1. Create `~/.nanobot/workspace/skills/my-skill/SKILL.md`
2. Add YAML frontmatter + markdown instructions
3. Auto-discovered on next run
