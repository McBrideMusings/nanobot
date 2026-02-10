"""WebSocket API channel for direct client connections."""

import json
import uuid

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import ApiConfig


class ApiChannel(BaseChannel):
    """
    WebSocket server channel for direct API access.

    Clients connect over WebSocket and exchange JSON messages:
      Inbound:  {"type": "message", "content": "hello"}
      Outbound: {"type": "response", "content": "Hi!"}
    """

    name = "api"

    def __init__(self, config: ApiConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: ApiConfig = config
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
        conn_id = uuid.uuid4().hex[:8]
        self._connections[conn_id] = ws
        remote = ws.remote_address
        logger.info(f"API: client connected {conn_id} from {remote}")

        try:
            async for raw in ws:
                await self._process_message(ws, conn_id, raw)
        except Exception as e:
            logger.debug(f"API: connection {conn_id} closed: {e}")
        finally:
            self._connections.pop(conn_id, None)
            logger.info(f"API: client disconnected {conn_id}")

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
