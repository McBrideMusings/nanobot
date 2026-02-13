"""LiteLLM provider implementation for multi-provider support."""

import json
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import litellm
from litellm import acompletion
from loguru import logger

from nanobot.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderCapabilities,
    StreamChunk,
    ToolCallRequest,
)
from nanobot.providers.registry import find_by_model, find_gateway

# Cache TTL for auto-discovered capabilities (seconds)
_DISCOVERY_TTL = 300  # 5 minutes


class LiteLLMProvider(LLMProvider):
    """
    LLM provider using LiteLLM for multi-provider support.
    
    Supports OpenRouter, Anthropic, OpenAI, Gemini, MiniMax, and many other providers through
    a unified interface.  Provider-specific logic is driven by the registry
    (see providers/registry.py) — no if-elif chains needed here.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str = "anthropic/claude-opus-4-5",
        extra_headers: dict[str, str] | None = None,
        provider_name: str | None = None,
    ):
        super().__init__(api_key, api_base)
        self.default_model = default_model
        self.extra_headers = extra_headers or {}

        # Detect gateway / local deployment.
        # provider_name (from config key) is the primary signal;
        # api_key / api_base are fallback for auto-detection.
        self._gateway = find_gateway(provider_name, api_key, api_base)

        # Configure environment variables
        if api_key:
            self._setup_env(api_key, api_base, default_model)

        if api_base:
            litellm.api_base = api_base

        # Discovery cache
        self._capabilities: ProviderCapabilities | None = None
        self._capabilities_ts: float = 0.0

        # Disable LiteLLM logging noise
        litellm.suppress_debug_info = True
        # Drop unsupported parameters for providers (e.g., gpt-5 rejects some params)
        litellm.drop_params = True

    def _setup_env(self, api_key: str, api_base: str | None, model: str) -> None:
        """Set environment variables based on detected provider."""
        spec = self._gateway or find_by_model(model)
        if not spec:
            return

        # Gateway/local overrides existing env; standard provider doesn't
        if self._gateway:
            os.environ[spec.env_key] = api_key
        else:
            os.environ.setdefault(spec.env_key, api_key)

        # Resolve env_extras placeholders:
        #   {api_key}  → user's API key
        #   {api_base} → user's api_base, falling back to spec.default_api_base
        effective_base = api_base or spec.default_api_base
        for env_name, env_val in spec.env_extras:
            resolved = env_val.replace("{api_key}", api_key)
            resolved = resolved.replace("{api_base}", effective_base)
            os.environ.setdefault(env_name, resolved)

    def _resolve_model(self, model: str) -> str:
        """Resolve model name by applying provider/gateway prefixes."""
        if self._gateway:
            # Gateway mode: apply gateway prefix, skip provider-specific prefixes
            prefix = self._gateway.litellm_prefix
            if self._gateway.strip_model_prefix:
                model = model.split("/")[-1]
            if prefix and not model.startswith(f"{prefix}/"):
                model = f"{prefix}/{model}"
            return model

        # Standard mode: auto-prefix for known providers
        spec = find_by_model(model)
        if spec and spec.litellm_prefix:
            if not any(model.startswith(s) for s in spec.skip_prefixes):
                model = f"{spec.litellm_prefix}/{model}"

        return model

    def _apply_model_overrides(self, model: str, kwargs: dict[str, Any]) -> None:
        """Apply model-specific parameter overrides from the registry."""
        model_lower = model.lower()
        spec = find_by_model(model)
        if spec:
            for pattern, overrides in spec.model_overrides:
                if pattern in model_lower:
                    kwargs.update(overrides)
                    return

    async def discover(self) -> ProviderCapabilities | None:
        """Query the provider for model capabilities (model name, context window).

        Results are cached for _DISCOVERY_TTL seconds. Returns None if the
        provider does not expose a /v1/models endpoint (e.g. hosted APIs).
        """
        # Return cache if fresh
        if self._capabilities and (time.monotonic() - self._capabilities_ts) < _DISCOVERY_TTL:
            return self._capabilities

        if not self.api_base:
            return None

        base = self.api_base.rstrip("/")
        url = f"{base}/models"
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                body = resp.json()

            models = body.get("data", [])
            if not models:
                return None

            entry = models[0]
            model_id = entry.get("id", "")
            # vLLM exposes max_model_len; other providers may not
            context_window = (
                entry.get("max_model_len")
                or entry.get("context_window")
                or entry.get("context_length")
            )

            if not context_window:
                # Try litellm's built-in model info as fallback
                try:
                    context_window = litellm.get_max_tokens(model_id)
                except Exception:
                    context_window = None

            if not context_window:
                context_window = 8192  # conservative default

            self._capabilities = ProviderCapabilities(
                model=model_id,
                context_window=int(context_window),
            )
            self._capabilities_ts = time.monotonic()
            logger.info(
                f"Discovered model: {self._capabilities.model}, "
                f"context_window: {self._capabilities.context_window}"
            )
            return self._capabilities

        except Exception as e:
            logger.debug(f"Model discovery failed: {e}")
            return self._capabilities  # return stale cache if any

    def invalidate(self) -> None:
        """Expire the cache so the next discover() re-queries the provider.

        We keep the stale capabilities as fallback in case re-discovery fails
        (e.g. network error). Only the timestamp is reset so the TTL check
        triggers a fresh query.
        """
        self._capabilities_ts = 0.0

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat completion request via LiteLLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions in OpenAI format.
            model: Model identifier (e.g., 'anthropic/claude-sonnet-4-5').
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
        
        Returns:
            LLMResponse with content and/or tool calls.
        """
        model = self._resolve_model(model or self.default_model)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Apply model-specific overrides (e.g. kimi-k2.5 temperature)
        self._apply_model_overrides(model, kwargs)

        # Pass api_key directly — more reliable than env vars alone
        if self.api_key:
            kwargs["api_key"] = self.api_key

        # Pass api_base for custom endpoints
        if self.api_base:
            kwargs["api_base"] = self.api_base

        # Pass extra headers (e.g. APP-Code for AiHubMix)
        if self.extra_headers:
            kwargs["extra_headers"] = self.extra_headers

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await acompletion(**kwargs)
            return self._parse_response(response)
        except litellm.ContextWindowExceededError as e:
            logger.warning(f"Context window exceeded: {e}")
            self.invalidate()
            return LLMResponse(
                content=f"Context window exceeded: {str(e)}",
                finish_reason="context_overflow",
            )
        except Exception as e:
            # Return error as content for graceful handling
            return LLMResponse(
                content=f"Error calling LLM: {str(e)}",
                finish_reason="error",
            )

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse LiteLLM response into our standard format."""
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                # Parse arguments from JSON string if needed
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                tool_calls.append(ToolCallRequest(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))

        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        reasoning_content = getattr(message, "reasoning_content", None)

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
            reasoning_content=reasoning_content,
        )

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a chat completion via LiteLLM."""
        model = self._resolve_model(model or self.default_model)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        self._apply_model_overrides(model, kwargs)

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.extra_headers:
            kwargs["extra_headers"] = self.extra_headers
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Accumulated tool calls across chunks
        accumulated_tool_calls: dict[int, dict[str, Any]] = {}

        try:
            response = await acompletion(**kwargs)
            async for chunk in response:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue

                delta = choice.delta
                finish_reason = choice.finish_reason

                # Accumulate tool call deltas
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc_delta.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        entry = accumulated_tool_calls[idx]
                        if tc_delta.id:
                            entry["id"] = tc_delta.id
                        if hasattr(tc_delta, "function") and tc_delta.function:
                            if tc_delta.function.name:
                                entry["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                entry["arguments"] += tc_delta.function.arguments

                delta_content = getattr(delta, "content", None)

                # Build final tool calls list if we have accumulated any
                tc_list = None
                if accumulated_tool_calls and finish_reason:
                    tc_list = []
                    for _idx, tc in sorted(accumulated_tool_calls.items()):
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {"raw": tc["arguments"]}
                        tc_list.append(ToolCallRequest(
                            id=tc["id"], name=tc["name"], arguments=args,
                        ))

                yield StreamChunk(
                    delta_content=delta_content,
                    tool_calls=tc_list,
                    finish_reason=finish_reason,
                )

        except litellm.ContextWindowExceededError as e:
            logger.warning(f"Context window exceeded (stream): {e}")
            self.invalidate()
            yield StreamChunk(
                delta_content=f"Context window exceeded: {str(e)}",
                finish_reason="context_overflow",
            )
        except Exception as e:
            yield StreamChunk(
                delta_content=f"Error calling LLM: {str(e)}",
                finish_reason="error",
            )

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.default_model
