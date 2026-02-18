<!-- Migrated to GitHub Issues on 2026-02-17. See https://github.com/McBrideMusings/nanobot/issues/3 -->
---
title: Memory Search Tool
status: backlog
priority: medium
tags:
  - tool
id: 4
---

# Memory Search

**Priority:** Medium
**Effort:** Low-Medium (~80-150 lines depending on approach)
**Impact:** Prevents memory from becoming useless as it grows

## Problem

Nanobot stores long-term memory in `MEMORY.md` and daily notes in `memory/YYYY-MM-DD.md`. All of MEMORY.md is loaded into the system prompt every time. Daily notes are loaded for the last N days.

As memories accumulate over weeks/months:
- MEMORY.md gets too large for the context window
- Old daily notes fall outside the N-day window and become invisible
- The agent has no way to search for something it wrote down three months ago
- Important context gets lost

## Solution

Add a `memory_search` tool that lets the agent search across all memory files.

## Approaches

### Approach A: Text Search (Recommended)

Simple grep-based search over all memory files. No dependencies, no infrastructure.

```python
class MemorySearchTool(Tool):
    name = "memory_search"
    description = "Search across all memory files (MEMORY.md and daily notes)"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term or phrase"},
            "max_results": {"type": "integer", "default": 10}
        },
        "required": ["query"]
    }
```

Implementation:
- Glob `memory/*.md` + `memory/MEMORY.md`
- Search each file for query string (case-insensitive)
- Return matching lines with surrounding context (3 lines before/after)
- Include filename and line number for each match
- Sort by recency (newest files first)

~50 lines of code. Good enough for a single user with months of notes.

### Approach B: Semantic Search

Embed memory chunks with a local model, store vectors, search by similarity.

- Requires embedding model (could use vLLM with an embedding model, or a small local one)
- Store embeddings in SQLite with `sqlite-vec` extension
- Chunk memory files into paragraphs
- Re-embed on file change (watch for modifications)

~200-300 lines. More powerful but adds significant complexity and a dependency on an embedding model.

### Recommendation

**Start with Approach A.** Text search is instant, has zero dependencies, and will work fine until you have thousands of memory entries. If it becomes insufficient, Approach B can be added later without changing the tool interface.

## Integration

### New File

- `nanobot/agent/tools/memory_search.py` - The search tool

### Changes

- `nanobot/agent/loop.py` - Register the tool in `_register_default_tools()`

### Tool Behavior

```
Agent calls: memory_search(query="ErsatzTV")

Returns:
--- memory/2026-02-15.md (line 12) ---
Set up ErsatzTV skill for Pierce. The API endpoint is at
http://100.114.249.118:8409. Created a schedule for the
retro cartoons channel running Saturday mornings.
---
```

## Complementary Change: Memory Pruning

As a follow-up, consider adding guidance in AGENTS.md for the agent to periodically consolidate daily notes into MEMORY.md (e.g., during heartbeat). This keeps the memory tidy:

- Daily notes capture raw events
- MEMORY.md stores distilled, long-term facts
- Agent can be instructed to review and consolidate weekly

## Testing

- Create a few test memory files with known content
- Verify search returns correct matches with context
- Verify empty results for non-matching queries
- Verify results are sorted by recency
