# Troubleshooting

## vLLM: "auto" tool choice requires --enable-auto-tool-choice

**Error:**
```
Error calling LLM: litellm.BadRequestError: "auto" tool choice requires --enable-auto-tool-choice server flag
```

**Cause:** vLLM requires the `--enable-auto-tool-choice` flag at startup to support tool calling.

**Fix:** Restart vLLM with the flag:
```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000 --enable-auto-tool-choice
```

This is a server-side config issue, not a nanobot bug.

## WhatsApp: QR Code Not Appearing

WhatsApp requires Node.js 18+. Verify:
```bash
node --version
```

Run the login process:
```bash
nanobot channels login
```

Scan the QR code with WhatsApp > Settings > Linked Devices.

## Provider Not Detected

If `nanobot status` doesn't show your provider:
1. Check `~/.nanobot/config.json` has the provider section with a valid `apiKey`
2. Model name must contain a keyword the provider recognizes (e.g., `claude` for Anthropic)
3. For gateways (OpenRouter), the API key prefix is used for detection (`sk-or-`)

## Channel Not Starting

Check:
1. Channel is `"enabled": true` in config
2. Required credentials are set (token, apiKey, etc.)
3. Run `nanobot channels status` for diagnostics
4. Check logs: `nanobot gateway` with `--logs` or `./nanobot-logs.sh`

## Shell Commands Timing Out

The `exec` tool has a 60-second default timeout. For longer commands:
1. Increase timeout in config: `"tools": {"exec": {"timeout": 120}}`
2. Or use the planned [Background Process Tool](/tickets/13)

## Session/Memory Issues

Session files: `~/.nanobot/sessions/*.jsonl`
Memory files: `~/.nanobot/workspace/memory/`

To reset a conversation:
- Send `/reset` in the chat channel
- Or delete the session file manually

To clear all memory:
- Edit/delete `~/.nanobot/workspace/memory/MEMORY.md`
