# Background Process Tool

**Priority:** Low-Medium
**Effort:** Low (~80-100 lines)
**Impact:** Lets the agent manage long-running shell commands

## Problem

The current `exec` tool runs a shell command synchronously with a 60-second timeout. This means the agent cannot:
- Start a long-running process and check on it later
- Monitor a log file in the background
- Run a build that takes several minutes
- Start a service and verify it's healthy

## Solution

Add a `process` tool for managing background shell processes.

## Tool Design

```python
class ProcessTool(Tool):
    name = "process"
    description = "Start, check, or stop background shell processes"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "status", "output", "stop", "list"],
                "description": "Action to perform"
            },
            "command": {
                "type": "string",
                "description": "Shell command to run (for 'start' action)"
            },
            "pid": {
                "type": "string",
                "description": "Process ID (for status/output/stop actions)"
            },
            "tail": {
                "type": "integer",
                "default": 50,
                "description": "Number of output lines to return (for 'output' action)"
            }
        },
        "required": ["action"]
    }
```

### Actions

- **start** - Launch a command in the background. Returns a process ID.
- **status** - Check if a process is still running, get exit code if finished.
- **output** - Get the last N lines of stdout/stderr from a process.
- **stop** - Kill a running process.
- **list** - List all tracked background processes with their status.

## Implementation

```python
class ProcessManager:
    """Manages background shell processes."""

    def __init__(self, max_processes=5):
        self._processes: dict[str, ProcessInfo] = {}
        self.max_processes = max_processes

    async def start(self, command: str, working_dir: str = None) -> str:
        """Start a background process, return its ID."""
        # Validate command against deny patterns (same as exec tool)
        # Create subprocess with stdout/stderr captured to temp files
        # Store ProcessInfo with pid, command, start_time, output_path
        # Return process ID

    def status(self, pid: str) -> dict:
        """Check process status."""
        # Return running/exited, exit code, runtime duration

    def output(self, pid: str, tail: int = 50) -> str:
        """Read last N lines of process output."""
        # Read from temp output file

    def stop(self, pid: str) -> str:
        """Kill a process."""
        # Send SIGTERM, wait briefly, SIGKILL if needed

    def list_all(self) -> list[dict]:
        """List all tracked processes."""
```

### Safety

- Same deny patterns as the `exec` tool (no rm -rf, dd, shutdown, etc.)
- Same workspace restriction when `restrictToWorkspace` is enabled
- Maximum 5 concurrent background processes (configurable)
- Processes are cleaned up when gateway stops
- Output files are capped at 1MB to prevent disk fill

## Use Cases

- `process start "docker logs -f ersatztv"` → monitor ErsatzTV logs
- `process start "nanobot cron list --watch"` → watch cron job execution
- `process start "curl -s http://localhost:8409/api/health"` → health check with no timeout pressure
- `process output abc123 --tail 20` → check what happened

## Integration

### New Files

- `nanobot/agent/tools/process.py` - Tool + ProcessManager

### Changes

- `nanobot/agent/loop.py` - Register in `_register_default_tools()`
- Process cleanup on gateway shutdown

## Testing

- Start a process (`sleep 10`), verify it's running, verify it stops
- Check output capture works
- Verify deny patterns are enforced
- Verify max process limit
