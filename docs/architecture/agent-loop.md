# Agent Loop

The agent loop is the heart of nanobot. It receives messages, builds context, calls the LLM, executes tools, and sends responses.

**File:** `nanobot/agent/loop.py`

## Processing Flow

1. **Message arrives** via the message bus (`InboundMessage`)
2. **Load session** — get or create session by `channel:chat_id`
3. **Build context** — system prompt + bootstrap files + memory + skills + conversation history
4. **Update tool context** — set current channel/chat_id for message, spawn, and cron tools
5. **Resolve model & context window** — auto-discover from provider or use config overrides
6. **Truncate history** — drop oldest history messages to fit within the context window budget
7. **Agent iteration loop** (max 20 iterations):
   - Call LLM with messages + tool definitions
   - If context overflow error → re-discover capabilities, re-truncate, retry once
   - If response contains tool calls → execute each tool, add results, continue loop
   - If no tool calls → break with final text response
8. **Save session** — persist updated conversation history
9. **Send response** — publish `OutboundMessage` to bus

## Tool Execution

Tools are registered in a `ToolRegistry`. Each tool is a Python class with:
- `name` — tool identifier
- `description` — what the tool does (shown to LLM)
- `parameters` — JSON schema for arguments
- `execute(args)` — the implementation

Built-in tools:

| Tool | Purpose |
|------|---------|
| `read_file` | Read file contents |
| `write_file` | Write content to file |
| `edit_file` | Replace text in file |
| `list_dir` | List directory contents |
| `exec` | Run shell commands |
| `web_search` | Brave Search API |
| `web_fetch` | Fetch and extract URL content |
| `message` | Send message to a channel |
| `spawn` | Start a background sub-agent |
| `cron` | Manage scheduled tasks |

## Sub-Agents

The `spawn` tool creates background sub-agents:
- Isolated tool registry (no `message`, no `spawn` — prevents recursion)
- Independent iteration loop (max 15 iterations)
- Results announced back to main agent via system messages
- Run as asyncio tasks

## Session Management

Sessions are keyed by `channel:chat_id` (e.g., `telegram:123456`, `api:default`). History is stored as JSONL files and loaded into context (last 50 messages).

## System Messages

The agent handles special "system" channel messages for:
- Sub-agent result announcements
- Heartbeat triggers
- Cron job execution

## Context Window Management

The agent automatically manages the context window to prevent overflow errors:

1. **Auto-discovery** — queries the provider's `/v1/models` endpoint for the model name and context window size. Results cached for 5 minutes.
2. **Budget calculation** — `input_budget = context_window - max_tokens - tool_definition_tokens`
3. **History truncation** — system prompt and current message are always kept. Oldest history messages are dropped first until the remaining messages fit within the budget.
4. **Safety net** — if a `ContextWindowExceededError` still occurs, capabilities are re-discovered, history is re-truncated, and the call is retried once.

Token estimation uses `len(json.dumps(messages)) // 3` (~3 chars per token) as a conservative heuristic. No external tokenizer dependency.

Config overrides (`contextWindow`, `maxTokens`) take priority over auto-discovered values. See [Providers](/guide/providers) for configuration.

## Error Handling

- LLM call failures return error text as content (no crash)
- Context window overflow triggers auto re-discovery and retry
- Tool execution errors return error strings (agent can retry or report)
- Max iteration limit prevents infinite tool loops
