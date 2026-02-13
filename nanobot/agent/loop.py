"""Agent loop: the core processing engine."""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.context import ContextBuilder
from nanobot.agent.subagent import SubagentManager
from nanobot.agent.tools.cron import CronTool
from nanobot.agent.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from nanobot.agent.tools.message import MessageTool
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.spawn import SpawnTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.bus.event_bus import AgentEvent, EventBus
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider, LLMResponse
from nanobot.session.manager import SessionManager


class AgentLoop:
    """
    The agent loop is the core processing engine.
    
    It:
    1. Receives messages from the bus
    2. Builds context with history, memory, skills
    3. Calls the LLM
    4. Executes tool calls
    5. Sends responses back
    """

    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int = 20,
        brave_api_key: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        cron_service: "CronService | None" = None,
        restrict_to_workspace: bool = False,
        session_manager: SessionManager | None = None,
        event_bus: EventBus | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        context_window: int | None = None,
    ):
        from nanobot.config.schema import ExecToolConfig
        self.bus = bus
        self.provider = provider
        self.workspace = workspace
        self._model_override = model  # None = auto-discover at runtime
        self.max_iterations = max_iterations
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()
        self.cron_service = cron_service
        self.restrict_to_workspace = restrict_to_workspace
        self.event_bus = event_bus
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.context_window = context_window  # None = auto-discover

        self.context = ContextBuilder(workspace)
        self.sessions = session_manager or SessionManager(workspace)
        self.tools = ToolRegistry()
        self.subagents = SubagentManager(
            provider=provider,
            workspace=workspace,
            bus=bus,
            model=self._model_override,
            brave_api_key=brave_api_key,
            exec_config=self.exec_config,
            restrict_to_workspace=restrict_to_workspace,
            event_bus=event_bus,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        self._running = False
        self._register_default_tools()

    async def _emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Emit an agent event if the event bus is available."""
        if self.event_bus:
            await self.event_bus.publish(AgentEvent("agent", event, data or {}))

    async def _emit_stream(self, event: str, data: dict[str, Any]) -> None:
        """Emit a stream event via the event bus."""
        if self.event_bus:
            await self.event_bus.publish(AgentEvent("stream", event, data))

    async def _call_llm_streaming(
        self,
        messages: list[dict[str, Any]],
        tool_defs: list[dict[str, Any]] | None,
        model: str,
    ) -> LLMResponse:
        """Call the LLM with streaming, emitting stream events as chunks arrive.

        Returns the final assembled LLMResponse (same shape as non-streaming).
        """
        msg_id = uuid.uuid4().hex[:12]
        await self._emit_stream("stream_start", {"id": msg_id})

        content_parts: list[str] = []
        tool_calls = None
        finish_reason = "stop"

        async for chunk in self.provider.stream_chat(
            messages=messages,
            tools=tool_defs,
            model=model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        ):
            if chunk.delta_content:
                content_parts.append(chunk.delta_content)
                await self._emit_stream("stream_chunk", {
                    "id": msg_id, "delta": chunk.delta_content,
                })
            if chunk.tool_calls is not None:
                tool_calls = chunk.tool_calls
            if chunk.finish_reason:
                finish_reason = chunk.finish_reason

        await self._emit_stream("stream_end", {"id": msg_id})

        return LLMResponse(
            content="".join(content_parts) if content_parts else None,
            tool_calls=tool_calls or [],
            finish_reason=finish_reason,
        )

    def _register_default_tools(self) -> None:
        """Register the default set of tools."""
        # File tools (restrict to workspace if configured)
        allowed_dir = self.workspace if self.restrict_to_workspace else None
        self.tools.register(ReadFileTool(allowed_dir=allowed_dir))
        self.tools.register(WriteFileTool(allowed_dir=allowed_dir))
        self.tools.register(EditFileTool(allowed_dir=allowed_dir))
        self.tools.register(ListDirTool(allowed_dir=allowed_dir))

        # Shell tool
        self.tools.register(ExecTool(
            working_dir=str(self.workspace),
            timeout=self.exec_config.timeout,
            restrict_to_workspace=self.restrict_to_workspace,
        ))

        # Web tools
        self.tools.register(WebSearchTool(api_key=self.brave_api_key))
        self.tools.register(WebFetchTool())

        # Message tool
        message_tool = MessageTool(send_callback=self.bus.publish_outbound)
        self.tools.register(message_tool)

        # Spawn tool (for subagents)
        spawn_tool = SpawnTool(manager=self.subagents)
        self.tools.register(spawn_tool)

        # Cron tool (for scheduling)
        if self.cron_service:
            self.tools.register(CronTool(self.cron_service))

    async def run(self) -> None:
        """Run the agent loop, processing messages from the bus."""
        self._running = True
        logger.info("Agent loop started")

        while self._running:
            try:
                # Wait for next message
                msg = await asyncio.wait_for(
                    self.bus.consume_inbound(),
                    timeout=1.0
                )

                # Process it
                try:
                    response = await self._process_message(msg)
                    if response:
                        await self.bus.publish_outbound(response)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Send error response
                    await self.bus.publish_outbound(OutboundMessage(
                        channel=msg.channel,
                        chat_id=msg.chat_id,
                        content=f"Sorry, I encountered an error: {str(e)}",
                        metadata=msg.metadata or {},
                    ))
            except asyncio.TimeoutError:
                continue

    def stop(self) -> None:
        """Stop the agent loop."""
        self._running = False
        logger.info("Agent loop stopping")

    async def _get_model(self) -> str:
        """Get the effective model name (config override > auto-discovery > provider default)."""
        if self._model_override:
            return self._model_override
        caps = await self.provider.discover()
        if caps:
            return caps.model
        return self.provider.get_default_model()

    async def _get_context_window(self) -> int:
        """Get the effective context window size (config override > auto-discovery > fallback)."""
        if self.context_window is not None:
            return self.context_window
        caps = await self.provider.discover()
        if caps:
            return caps.context_window
        return 8192

    async def _prepare_context(
        self, messages: list[dict[str, Any]], tool_defs: list[dict[str, Any]] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Resolve model, compute budget, and truncate messages.

        Returns (model_name, truncated_messages).
        """
        model = await self._get_model()
        context_window = await self._get_context_window()
        input_budget = context_window - self.max_tokens
        tool_tokens = self._estimate_tokens(tool_defs) if tool_defs else 0
        message_budget = input_budget - tool_tokens
        if message_budget <= 0:
            logger.warning(
                f"Input budget is non-positive ({message_budget}): "
                f"context_window={context_window}, max_tokens={self.max_tokens}, "
                f"tool_tokens={tool_tokens}"
            )
        messages = self._truncate_to_budget(messages, message_budget)
        return model, messages

    @staticmethod
    def _estimate_tokens(messages: list[dict[str, Any]]) -> int:
        """Estimate token count from messages (~3 chars per token, intentionally conservative)."""
        return len(json.dumps(messages, ensure_ascii=False)) // 3

    @staticmethod
    def _truncate_to_budget(
        messages: list[dict[str, Any]], budget: int
    ) -> list[dict[str, Any]]:
        """Truncate history messages (oldest first) to fit within a token budget.

        The first message (system prompt) and last message (current user message)
        are always kept. History messages in between are dropped from oldest first.
        """
        if len(messages) <= 2:
            return messages

        system = messages[0]
        current = messages[-1]
        history = messages[1:-1]

        # Fixed cost: system + current message
        fixed_tokens = AgentLoop._estimate_tokens([system, current])
        remaining = budget - fixed_tokens
        if remaining <= 0:
            return [system, current]

        # Keep as many recent history messages as fit
        kept: list[dict[str, Any]] = []
        for msg in reversed(history):
            msg_tokens = AgentLoop._estimate_tokens([msg])
            if remaining - msg_tokens < 0:
                break
            kept.append(msg)
            remaining -= msg_tokens

        kept.reverse()
        if len(kept) < len(history):
            dropped = len(history) - len(kept)
            logger.info(f"Truncated {dropped} history messages to fit context window")

        return [system] + kept + [current]

    async def _process_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        Process a single inbound message.
        
        Args:
            msg: The inbound message to process.
        
        Returns:
            The response message, or None if no response needed.
        """
        # Handle system messages (subagent announces)
        # The chat_id contains the original "channel:chat_id" to route back to
        if msg.channel == "system":
            return await self._process_system_message(msg)

        preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        logger.info(f"Processing message from {msg.channel}:{msg.sender_id}: {preview}")

        # Get or create session
        session = self.sessions.get_or_create(msg.session_key)

        # Update tool contexts
        message_tool = self.tools.get("message")
        if isinstance(message_tool, MessageTool):
            message_tool.set_context(msg.channel, msg.chat_id)

        spawn_tool = self.tools.get("spawn")
        if isinstance(spawn_tool, SpawnTool):
            spawn_tool.set_context(msg.channel, msg.chat_id)

        cron_tool = self.tools.get("cron")
        if isinstance(cron_tool, CronTool):
            cron_tool.set_context(msg.channel, msg.chat_id)

        # Build initial messages (use get_history for LLM-formatted messages)
        messages = self.context.build_messages(
            history=session.get_history(),
            current_message=msg.content,
            media=msg.media if msg.media else None,
            channel=msg.channel,
            chat_id=msg.chat_id,
        )

        # Resolve model, truncate history to fit context window
        tool_defs = self.tools.get_definitions()
        model, messages = await self._prepare_context(messages, tool_defs)

        # Agent loop
        iteration = 0
        final_content = None

        while iteration < self.max_iterations:
            iteration += 1
            await self._emit("thinking_started", {"iteration": iteration})

            # Call LLM with streaming (emits stream_start/chunk/end events)
            response = await self._call_llm_streaming(messages, tool_defs, model)

            # Retry once on context overflow after re-discovery
            if response.finish_reason == "context_overflow":
                logger.warning("Context overflow — re-discovering capabilities and retrying")
                model, messages = await self._prepare_context(messages, tool_defs)
                response = await self._call_llm_streaming(messages, tool_defs, model)

            if response.finish_reason == "context_overflow":
                final_content = "I'm sorry, the message is too long for my context window. Please try a shorter message or start a new session."
                break

            # Handle tool calls
            if response.has_tool_calls:
                # Add assistant message with tool calls
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)  # Must be JSON string
                        }
                    }
                    for tc in response.tool_calls
                ]
                messages = self.context.add_assistant_message(
                    messages, response.content, tool_call_dicts,
                    reasoning_content=response.reasoning_content,
                )

                # Execute tools
                for tool_call in response.tool_calls:
                    args_str = json.dumps(tool_call.arguments, ensure_ascii=False)
                    logger.info(f"Tool call: {tool_call.name}({args_str[:200]})")
                    await self._emit("tool_call", {
                        "name": tool_call.name,
                        "args": tool_call.arguments,
                        "iteration": iteration,
                    })
                    t0 = time.monotonic()
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    await self._emit("tool_result", {
                        "name": tool_call.name,
                        "result_preview": result[:200] if result else "",
                        "duration_ms": duration_ms,
                    })
                    messages = self.context.add_tool_result(
                        messages, tool_call.id, tool_call.name, result
                    )
            else:
                # No tool calls, we're done
                final_content = response.content
                await self._emit("thinking_finished", {"iterations": iteration})
                break

        if final_content is None:
            final_content = "I've completed processing but have no response to give."
            await self._emit("thinking_finished", {"iterations": iteration})

        # Log response preview
        preview = final_content[:120] + "..." if len(final_content) > 120 else final_content
        logger.info(f"Response to {msg.channel}:{msg.sender_id}: {preview}")

        # Save to session
        session.add_message("user", msg.content)
        session.add_message("assistant", final_content)
        self.sessions.save(session)

        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=final_content,
            metadata=msg.metadata or {},  # Pass through for channel-specific needs (e.g. Slack thread_ts)
        )

    async def _process_system_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        Process a system message (e.g., subagent announce).
        
        The chat_id field contains "original_channel:original_chat_id" to route
        the response back to the correct destination.
        """
        logger.info(f"Processing system message from {msg.sender_id}")

        # Parse origin from chat_id (format: "channel:chat_id")
        if ":" in msg.chat_id:
            parts = msg.chat_id.split(":", 1)
            origin_channel = parts[0]
            origin_chat_id = parts[1]
        else:
            # Fallback
            origin_channel = "cli"
            origin_chat_id = msg.chat_id

        # Use the origin session for context
        session_key = f"{origin_channel}:{origin_chat_id}"
        session = self.sessions.get_or_create(session_key)

        # Update tool contexts
        message_tool = self.tools.get("message")
        if isinstance(message_tool, MessageTool):
            message_tool.set_context(origin_channel, origin_chat_id)

        spawn_tool = self.tools.get("spawn")
        if isinstance(spawn_tool, SpawnTool):
            spawn_tool.set_context(origin_channel, origin_chat_id)

        cron_tool = self.tools.get("cron")
        if isinstance(cron_tool, CronTool):
            cron_tool.set_context(origin_channel, origin_chat_id)

        # Build messages with the announce content
        messages = self.context.build_messages(
            history=session.get_history(),
            current_message=msg.content,
            channel=origin_channel,
            chat_id=origin_chat_id,
        )

        # Resolve model, truncate history to fit context window
        tool_defs = self.tools.get_definitions()
        model, messages = await self._prepare_context(messages, tool_defs)

        # Agent loop (limited for announce handling)
        iteration = 0
        final_content = None

        while iteration < self.max_iterations:
            iteration += 1
            await self._emit("thinking_started", {"iteration": iteration})

            response = await self._call_llm_streaming(messages, tool_defs, model)

            if response.finish_reason == "context_overflow":
                logger.warning("Context overflow — re-discovering capabilities and retrying")
                model, messages = await self._prepare_context(messages, tool_defs)
                response = await self._call_llm_streaming(messages, tool_defs, model)

            if response.finish_reason == "context_overflow":
                final_content = "Background task could not complete — context window exceeded."
                break

            if response.has_tool_calls:
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    }
                    for tc in response.tool_calls
                ]
                messages = self.context.add_assistant_message(
                    messages, response.content, tool_call_dicts,
                    reasoning_content=response.reasoning_content,
                )

                for tool_call in response.tool_calls:
                    args_str = json.dumps(tool_call.arguments, ensure_ascii=False)
                    logger.info(f"Tool call: {tool_call.name}({args_str[:200]})")
                    await self._emit("tool_call", {
                        "name": tool_call.name,
                        "args": tool_call.arguments,
                        "iteration": iteration,
                    })
                    t0 = time.monotonic()
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    await self._emit("tool_result", {
                        "name": tool_call.name,
                        "result_preview": result[:200] if result else "",
                        "duration_ms": duration_ms,
                    })
                    messages = self.context.add_tool_result(
                        messages, tool_call.id, tool_call.name, result
                    )
            else:
                final_content = response.content
                await self._emit("thinking_finished", {"iterations": iteration})
                break

        if final_content is None:
            final_content = "Background task completed."
            await self._emit("thinking_finished", {"iterations": iteration})

        # Save to session (mark as system message in history)
        session.add_message("user", f"[System: {msg.sender_id}] {msg.content}")
        session.add_message("assistant", final_content)
        self.sessions.save(session)

        return OutboundMessage(
            channel=origin_channel,
            chat_id=origin_chat_id,
            content=final_content
        )

    async def process_direct(
        self,
        content: str,
        session_key: str = "cli:direct",
        channel: str = "cli",
        chat_id: str = "direct",
    ) -> str:
        """
        Process a message directly (for CLI or cron usage).
        
        Args:
            content: The message content.
            session_key: Session identifier.
            channel: Source channel (for context).
            chat_id: Source chat ID (for context).
        
        Returns:
            The agent's response.
        """
        msg = InboundMessage(
            channel=channel,
            sender_id="user",
            chat_id=chat_id,
            content=content
        )

        response = await self._process_message(msg)
        return response.content if response else ""
