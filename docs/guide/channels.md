# Channels

Nanobot connects to chat platforms via channels. Each channel runs independently and routes messages through the message bus to the agent.

## Supported Channels

| Channel | Transport | Auth | Setup Difficulty |
|---------|-----------|------|------------------|
| **Telegram** | Long polling | Bot token | Easy |
| **Discord** | WebSocket | Bot token + intents | Easy |
| **WhatsApp** | Node.js bridge (Baileys) | QR code scan | Medium |
| **Feishu/Lark** | WebSocket | App ID + Secret | Medium |
| **DingTalk** | Stream mode | Client ID + Secret | Medium |
| **Slack** | Socket mode | Bot token + App token | Medium |
| **Email** | IMAP/SMTP | Email credentials | Medium |
| **QQ** | WebSocket (botpy) | App ID + Secret | Easy |
| **API** | WebSocket | None (direct) | Easy |

All channels (except API) support access control via `allowFrom` lists.

## Configuration

Channels are configured in `~/.nanobot/config.json` under `channels`:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

## Telegram

1. Create a bot via `@BotFather` in Telegram
2. Copy the bot token
3. Add to config with your user ID in `allowFrom`
4. Run `nanobot gateway`

## Discord

1. Create an app at [discord.com/developers](https://discord.com/developers/applications)
2. Enable **MESSAGE CONTENT INTENT** in Bot settings
3. Copy bot token, get your User ID (Developer Mode > right-click avatar)
4. Add to config, invite bot to your server with `Send Messages` + `Read Message History` permissions

## Slack

Uses Socket Mode (no public URL needed):

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "botToken": "xoxb-...",
      "appToken": "xapp-...",
      "groupPolicy": "mention"
    }
  }
}
```

Group policies: `"mention"` (respond when @mentioned), `"open"` (respond to all), `"allowlist"` (specific channels only).

## API (WebSocket)

Direct WebSocket connection for custom clients. Used by the NanobotChat SwiftUI app.

```json
{
  "channels": {
    "api": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 18790
    }
  }
}
```

Connect to `ws://host:port/ws` and exchange JSON messages.

## Access Control

Every channel supports `allowFrom`:
- Empty list `[]` = allow everyone
- Non-empty list = only listed users can interact
- Format varies by channel (user IDs, phone numbers, email addresses)

See the [README](https://github.com/McBrideMusings/nanobot) for full setup instructions per channel.
