# Deployment

## Docker

Nanobot ships with a Dockerfile (Python 3.12 + Node.js 20).

### Build and Run

```bash
# Build
docker build -t nanobot .

# Initialize (first time)
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot onboard

# Edit config
vim ~/.nanobot/config.json

# Run gateway
docker run -v ~/.nanobot:/root/.nanobot -p 18790:18790 nanobot gateway

# One-shot command
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot agent -m "Hello!"
```

The `-v ~/.nanobot:/root/.nanobot` mount persists config, workspace, and sessions across container restarts.

### Pierce's UnRAID Setup

Build and run script at project root:

```bash
./nanobot.sh        # Build and run
./nanobot-logs.sh   # View logs
```

| Setting | Value |
|---------|-------|
| Bind address | 100.114.249.118 (Tailscale) |
| Gateway port | 18790 |
| App data | /mnt/user/appdata/nanobot/ |
| Config | /mnt/user/appdata/nanobot/config.json |
| Workspace | /mnt/user/appdata/nanobot/workspace/ |

The container is not exposed to the public internet — only accessible via Tailscale.

## Gateway

The gateway starts all enabled channels, the message bus, heartbeat service, cron service, and the API WebSocket server:

```bash
nanobot gateway
```

Configuration:

```json
{
  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  }
}
```
