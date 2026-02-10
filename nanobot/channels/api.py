"""WebSocket API channel for direct client connections."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import ApiConfig

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager


class ApiChannel(BaseChannel):
    """
    WebSocket server channel for direct API access.

    Clients connect over WebSocket and exchange JSON messages:
      Inbound:  {"type": "message", "content": "hello"}
      Outbound: {"type": "response", "content": "Hi!"}

    Clients may pass ?session_id=<id> to resume a persistent session.
    On connect the server replays the session history so all clients
    stay in sync.
    """

    name = "api"

    def __init__(self, config: ApiConfig, bus: MessageBus,
                 session_manager: SessionManager | None = None):
        super().__init__(config, bus)
        self.config: ApiConfig = config
        self.session_manager = session_manager
        self._server = None
        self._connections: dict[str, object] = {}

    async def start(self) -> None:
        """Start the WebSocket server."""
        import websockets

        self._running = True
        host = self.config.host
        port = self.config.port

        self._server = await websockets.serve(self._handler, host, port)
        logger.info(f"API channel listening on ws://{host}:{port}")

        await self._server.wait_closed()

    async def stop(self) -> None:
        """Stop the WebSocket server and close all connections."""
        self._running = False

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        self._connections.clear()

    async def send(self, msg: OutboundMessage) -> None:
        """Send a response to the client identified by chat_id."""
        ws = self._connections.get(msg.chat_id)
        if not ws:
            logger.warning(f"API: no connection for chat_id {msg.chat_id}")
            return

        try:
            payload = json.dumps({"type": "response", "content": msg.content})
            await ws.send(payload)
        except Exception as e:
            logger.error(f"API send error: {e}")

    async def _handler(self, ws) -> None:
        """Handle a single WebSocket connection."""
        session_id = self._parse_session_id(ws) or uuid.uuid4().hex[:8]
        self._connections[session_id] = ws
        remote = ws.remote_address
        logger.info(f"API: client connected session={session_id} from {remote}")

        await self._send_history(ws, session_id)

        try:
            async for raw in ws:
                await self._process_message(ws, session_id, raw)
        except Exception as e:
            logger.debug(f"API: connection {session_id} closed: {e}")
        finally:
            self._connections.pop(session_id, None)
            logger.info(f"API: client disconnected {session_id}")

    @staticmethod
    def _parse_session_id(ws) -> str | None:
        """Extract session_id query parameter from the WebSocket request."""
        try:
            # New API (websockets 13+): ws.request.path
            # Legacy API (websockets 10-12): ws.path
            if hasattr(ws, "request") and ws.request is not None:
                path = ws.request.path
            elif hasattr(ws, "path"):
                path = ws.path
            else:
                logger.warning("API: cannot read request path from websocket object")
                return None

            logger.debug(f"API: raw websocket path = {path!r}")
            params = parse_qs(urlparse(path).query)
            val = params.get("session_id", [None])[0]
            if not val:
                logger.debug(f"API: no session_id query param in path")
            return val if val else None
        except Exception as e:
            logger.error(f"API: failed to parse session_id: {e}")
            return None

    async def _send_history(self, ws, session_id: str) -> None:
        """Send existing session history to a newly connected client."""
        if not self.session_manager:
            logger.warning("API: no session_manager, cannot send history")
            return

        session_key = f"{self.name}:{session_id}"
        session = self.session_manager.get_or_create(session_key)
        if not session.messages:
            logger.debug(f"API: no history for session {session_key}")
            return

        history = [{"role": m["role"], "content": m["content"]}
                   for m in session.messages]
        payload = json.dumps({"type": "history", "messages": history})
        try:
            await ws.send(payload)
            logger.info(f"API: sent {len(history)} history messages to {session_id}")
        except Exception as e:
            logger.error(f"API: failed to send history: {e}")

    async def _process_message(self, ws, conn_id: str, raw: str) -> None:
        """Parse and route a single inbound message."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send(json.dumps({"type": "error", "content": "Invalid JSON"}))
            return

        msg_type = data.get("type")
        if msg_type != "message":
            await ws.send(json.dumps({"type": "error", "content": f"Unknown type: {msg_type}"}))
            return

        content = data.get("content", "")
        if not content:
            return

        await self._handle_message(
            sender_id=conn_id,
            chat_id=conn_id,
            content=content,
        )
