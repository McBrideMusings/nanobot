"""WebSocket API channel for direct client connections."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import ApiConfig

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager

FIXED_CHAT_ID = "default"


class ApiChannel(BaseChannel):
    """
    WebSocket server channel for direct API access.

    Clients connect over WebSocket and exchange JSON messages:
      Inbound:  {"type": "message", "content": "hello"}
      Outbound: {"type": "response", "content": "Hi!"}

    All connections share a single persistent session (api:default),
    matching how other channels (Telegram, Discord, Slack) work.
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
        self._latest_conn_id: str | None = None

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
        self._latest_conn_id = None

    async def send(self, msg: OutboundMessage) -> None:
        """Send a response to the client via conn_id in metadata."""
        conn_id = msg.metadata.get("_conn_id") if msg.metadata else None
        ws = self._connections.get(conn_id) if conn_id else None

        # Fallback: send to most recently connected client
        if not ws and self._latest_conn_id:
            ws = self._connections.get(self._latest_conn_id)

        if not ws:
            logger.warning(f"API: no connection for conn_id={conn_id}")
            return

        try:
            payload = json.dumps({"type": "response", "content": msg.content})
            await ws.send(payload)
        except Exception as e:
            logger.error(f"API send error: {e}")

    async def _handler(self, ws) -> None:
        """Handle a single WebSocket connection."""
        conn_id = uuid.uuid4().hex[:8]
        self._connections[conn_id] = ws
        self._latest_conn_id = conn_id
        remote = ws.remote_address
        logger.info(f"API: client connected conn={conn_id} from {remote}")

        await self._send_history(ws)

        try:
            async for raw in ws:
                await self._process_message(ws, conn_id, raw)
        except Exception as e:
            logger.debug(f"API: connection {conn_id} closed: {e}")
        finally:
            self._connections.pop(conn_id, None)
            if self._latest_conn_id == conn_id:
                self._latest_conn_id = None
            logger.info(f"API: client disconnected {conn_id}")

    async def _send_history(self, ws) -> None:
        """Send existing session history to a newly connected client."""
        if not self.session_manager:
            logger.warning("API: no session_manager, cannot send history")
            return

        session_key = f"{self.name}:{FIXED_CHAT_ID}"
        session = self.session_manager.get_or_create(session_key)
        if not session.messages:
            logger.debug(f"API: no history for session {session_key}")
            return

        history = [{"role": m["role"], "content": m["content"]}
                   for m in session.messages]
        payload = json.dumps({"type": "history", "messages": history})
        try:
            await ws.send(payload)
            logger.info(f"API: sent {len(history)} history messages")
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
            chat_id=FIXED_CHAT_ID,
            content=content,
            metadata={"_conn_id": conn_id},
        )
