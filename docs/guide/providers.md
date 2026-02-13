# Providers

Nanobot supports multiple LLM providers through a registry-based system. Adding a new provider takes just 2 steps.

## Supported Providers

| Provider | Purpose | Model Examples |
|----------|---------|----------------|
| **openrouter** | Gateway (any model) | Any model via OpenRouter |
| **anthropic** | Claude (direct) | claude-opus-4-5, claude-sonnet-4-5 |
| **openai** | GPT (direct) | gpt-4, gpt-4o |
| **deepseek** | DeepSeek (direct) | deepseek-chat, deepseek-r1 |
| **gemini** | Google Gemini | gemini-pro, gemini-2.0 |
| **groq** | Groq + Whisper | llama-3, whisper-large-v3 |
| **dashscope** | Alibaba Qwen | qwen-max, qwen-plus |
| **moonshot** | Moonshot/Kimi | kimi-k2.5 |
| **zhipu** | Zhipu GLM | glm-4 |
| **aihubmix** | Gateway (OpenAI-compatible) | Any model via AiHubMix |
| **vllm** | Local server | Any model served via vLLM |

## Configuration

Providers are configured in `~/.nanobot/config.json`:

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    },
    "anthropic": {
      "apiKey": "sk-ant-xxx"
    },
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    }
  }
}
```

Each provider supports: `apiKey`, `apiBase`, `extraHeaders`.

### Agent Defaults

| Field | Default | Description |
|-------|---------|-------------|
| `model` | `""` (empty) | Model name. Empty = auto-discover from provider |
| `maxTokens` | `4096` | Output token budget |
| `contextWindow` | `null` | Total context window override. `null` = auto-discover |
| `temperature` | `0.7` | Sampling temperature |
| `maxToolIterations` | `20` | Max tool call rounds per message |

## Auto-Discovery (vLLM)

When `model` is empty (the default), nanobot queries the provider's `/v1/models` endpoint at runtime to discover the model name and context window. This is especially useful for local vLLM deployments — change the model on vLLM and nanobot adapts automatically:

```json
{
  "providers": {
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  },
  "agents": {
    "defaults": {
      "maxTokens": 4096
    }
  }
}
```

No `model` or `contextWindow` needed — both are discovered from vLLM. Discovery results are cached for 5 minutes and re-validated on errors.

You can override auto-discovery by setting explicit values:

```json
{
  "agents": {
    "defaults": {
      "model": "Qwen/Qwen3-32B-AWQ",
      "contextWindow": 32768
    }
  }
}
```

## Auto-Detection

Nanobot automatically detects which provider to use based on the model name:
- `claude-*` → anthropic
- `gpt-*` → openai
- `deepseek-*` → deepseek
- `qwen-*` → dashscope

Gateway providers (OpenRouter, AiHubMix) are detected by API key prefix or base URL.

## Model Prefixing

Models are automatically prefixed for LiteLLM routing:
- `qwen-max` → `dashscope/qwen-max`
- `deepseek-chat` → `deepseek/deepseek-chat`

Models that already have the correct prefix are not double-prefixed.

## Voice Transcription

Groq provides free voice transcription via Whisper. If configured, Telegram voice messages are automatically transcribed:

```json
{
  "providers": {
    "groq": {
      "apiKey": "gsk_xxx"
    }
  }
}
```

## Adding a New Provider

**Step 1.** Add a `ProviderSpec` to `PROVIDERS` in `nanobot/providers/registry.py`:

```python
ProviderSpec(
    name="myprovider",
    keywords=("myprovider", "mymodel"),
    env_key="MYPROVIDER_API_KEY",
    display_name="My Provider",
    litellm_prefix="myprovider",
    skip_prefixes=("myprovider/",),
)
```

**Step 2.** Add a field to `ProvidersConfig` in `nanobot/config/schema.py`:

```python
class ProvidersConfig(BaseModel):
    ...
    myprovider: ProviderConfig = ProviderConfig()
```

That's it. Environment variables, model prefixing, config matching, and `nanobot status` all work automatically.

## Check Status

```bash
nanobot status
```

Shows all configured providers, available models, and connection status.
