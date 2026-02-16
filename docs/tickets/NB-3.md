---
title: MCP Support
status: backlog
priority: high
tags:
  - tool
id: 3
---

# MCP (Model Context Protocol) Support

**Priority:** High
**Effort:** Medium (~200-300 lines)
**Impact:** Unlocks entire ecosystem of third-party integrations without custom tool code

## Problem

Adding new capabilities to nanobot currently requires writing a Python tool class, registering it in the agent loop, and redeploying. This is fine for core tools but doesn't scale when you want to connect to dozens of services (Notion, GitHub, databases, home automation, etc.).

## Solution

Implement MCP client support so nanobot can connect to external MCP servers and expose their tools to the agent dynamically at startup.

MCP (Model Context Protocol) is an open standard for connecting AI assistants to external data sources and tools. MCP servers are standalone processes that expose tools over stdio or SSE transports. Hundreds of MCP servers already exist for popular services.

## How It Works

1. User configures MCP servers in `config.json`
2. On gateway startup, nanobot spawns each MCP server as a child process (stdio) or connects via SSE
3. Nanobot discovers available tools from each server via the MCP `tools/list` method
4. Discovered tools are registered in the tool registry alongside built-in tools
5. When the agent calls an MCP tool, nanobot proxies the call to the MCP server and returns the result

## Configuration

```json
{
  "mcp": {
    "servers": {
      "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_TOKEN": "ghp_xxx"
        }
      },
      "sqlite": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/db.sqlite"]
      },
      "home-assistant": {
        "transport": "sse",
        "url": "http://100.114.249.118:8123/mcp",
        "headers": {
          "Authorization": "Bearer xxx"
        }
      }
    }
  }
}
```

## Architecture

### New Files

- `nanobot/mcp/client.py` - MCP client implementation
  - `McpStdioClient` - Manages a child process, speaks JSON-RPC over stdin/stdout
  - `McpSseClient` - Connects to SSE endpoint, speaks JSON-RPC over HTTP
  - `McpManager` - Lifecycle management for all configured servers

- `nanobot/agent/tools/mcp_proxy.py` - Tool wrapper
  - Dynamically creates `Tool` instances from MCP tool definitions
  - Proxies `execute()` calls to the MCP server
  - Converts MCP tool schemas to nanobot's JSON schema format

### Integration Points

- **Config schema** (`config/schema.py`): Add `McpConfig` with server definitions
- **Agent loop** (`agent/loop.py`): Start MCP manager before registering tools, register discovered tools
- **Gateway** (`gateway/`): Start/stop MCP servers with gateway lifecycle

### MCP Protocol (simplified)

```
Client -> Server: {"method": "initialize", "params": {...}}
Server -> Client: {"result": {"capabilities": {...}}}

Client -> Server: {"method": "tools/list"}
Server -> Client: {"result": {"tools": [{"name": "...", "inputSchema": {...}}]}}

Client -> Server: {"method": "tools/call", "params": {"name": "...", "arguments": {...}}}
Server -> Client: {"result": {"content": [{"type": "text", "text": "..."}]}}
```

### Tool Naming

MCP tools are registered with a namespace prefix to avoid collisions:
- MCP server "github" tool "create_issue" → tool name `github__create_issue`
- Description includes the server name for clarity

## Dependencies

- `mcp` Python package (official MCP SDK) - handles protocol details
- OR minimal implementation: just JSON-RPC over subprocess stdin/stdout (~150 lines)

The minimal approach is preferred to keep line count low. The MCP protocol over stdio is straightforward JSON-RPC - no need for a heavy SDK.

## Error Handling

- Server fails to start → log warning, skip that server, continue with others
- Server crashes mid-session → log error, remove its tools from registry, attempt restart
- Tool call timeout → return error string to agent (same pattern as other tools)
- Server not found (npx package missing) → clear error message at startup

## Testing

- Mock MCP server that exposes a simple echo tool
- Test tool discovery and registration
- Test tool execution round-trip
- Test server lifecycle (start, crash, restart)

## Example Use Cases

With MCP support, you could connect:
- **Home Assistant MCP** → control lights, check sensors, run automations
- **GitHub MCP** → manage issues, PRs, repos without the `gh` CLI
- **SQLite MCP** → query databases directly
- **Filesystem MCP** → scoped file access for specific directories
- **Custom MCP servers** → wrap any REST API as an MCP server

## Open Questions

- Should MCP servers be started lazily (on first tool call) or eagerly (at gateway startup)? Eager is simpler and avoids latency on first call.
- Should there be a tool count limit per server to avoid flooding the agent's tool list? OpenClaw doesn't seem to limit this.
- Should MCP resources (read-only data) also be supported, or just tools? Tools-only is simpler and covers 90% of use cases.
