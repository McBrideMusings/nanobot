"""WebSocket API channel for direct client connections."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import ApiConfig

if TYPE_CHECKING:
    from nanobot.bus.event_bus import AgentEvent, EventBus
    from nanobot.session.manager import SessionManager

FIXED_CHAT_ID = "default"

# Link preview cache: url -> (result_dict, timestamp)
_link_preview_cache: dict[str, tuple[dict[str, Any], float]] = {}
_LINK_PREVIEW_TTL = 600  # 10 minutes
_LINK_PREVIEW_MAX = 200  # max cached entries


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
                 session_manager: "SessionManager | None" = None,
                 event_bus: "EventBus | None" = None,
                 workspace: str = "~/.nanobot/workspace"):
        super().__init__(config, bus)
        self.config: ApiConfig = config
        self.session_manager = session_manager
        self.event_bus = event_bus
        self._server = None
        self._connections: dict[str, object] = {}
        self._latest_conn_id: str | None = None

        # Push notifications
        self._push_dir = Path(workspace).expanduser() / "push"
        self._vapid_keys: dict[str, str] | None = None
        self._push_subscriptions: list[dict[str, Any]] = []
        self._load_push_state()

    def _load_push_state(self) -> None:
        """Load VAPID keys and subscriptions from disk."""
        vapid_path = self._push_dir / "vapid.json"
        subs_path = self._push_dir / "subscriptions.json"

        if vapid_path.exists():
            try:
                self._vapid_keys = json.loads(vapid_path.read_text())
            except Exception as e:
                logger.warning(f"Failed to load VAPID keys: {e}")

        if subs_path.exists():
            try:
                self._push_subscriptions = json.loads(subs_path.read_text())
            except Exception as e:
                logger.warning(f"Failed to load push subscriptions: {e}")

    def _ensure_vapid_keys(self) -> dict[str, str]:
        """Generate or return existing VAPID key pair."""
        if self._vapid_keys:
            return self._vapid_keys

        import base64
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from py_vapid import Vapid

        vapid = Vapid()
        vapid.generate_keys()

        pub_raw = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        priv_raw = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")

        self._push_dir.mkdir(parents=True, exist_ok=True)
        vapid_path = self._push_dir / "vapid.json"

        self._vapid_keys = {
            "public_key": base64.urlsafe_b64encode(pub_raw).rstrip(b"=").decode(),
            "private_key": base64.urlsafe_b64encode(priv_raw).rstrip(b"=").decode(),
        }
        vapid_path.write_text(json.dumps(self._vapid_keys, indent=2))
        vapid_path.chmod(0o600)
        logger.info("Generated new VAPID key pair")
        return self._vapid_keys

    def _save_subscriptions(self) -> None:
        """Persist push subscriptions to disk."""
        self._push_dir.mkdir(parents=True, exist_ok=True)
        subs_path = self._push_dir / "subscriptions.json"
        subs_path.write_text(json.dumps(self._push_subscriptions, indent=2))

    def _add_subscription(self, subscription: dict[str, Any]) -> None:
        """Add a push subscription (dedup by endpoint)."""
        endpoint = subscription.get("endpoint", "")
        self._push_subscriptions = [
            s for s in self._push_subscriptions if s.get("endpoint") != endpoint
        ]
        self._push_subscriptions.append(subscription)
        self._save_subscriptions()
        logger.info(f"Push subscription added: {endpoint[:60]}...")

    def _remove_subscription(self, endpoint: str) -> None:
        """Remove a push subscription by endpoint."""
        self._push_subscriptions = [
            s for s in self._push_subscriptions if s.get("endpoint") != endpoint
        ]
        self._save_subscriptions()
        logger.info(f"Push subscription removed: {endpoint[:60]}...")

    async def _send_push_notification(self, title: str, body: str) -> None:
        """Send a web push notification to all subscribers (runs in thread)."""
        if not self._push_subscriptions or not self._vapid_keys:
            return
        await asyncio.to_thread(self._send_push_sync, title, body)

    def _send_push_sync(self, title: str, body: str) -> None:
        """Synchronous push sending, intended for asyncio.to_thread."""
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            logger.debug("pywebpush not available, skipping push")
            return

        data = json.dumps({"title": title, "body": body})
        dead_endpoints: list[str] = []

        for sub in self._push_subscriptions:
            try:
                webpush(
                    subscription_info=sub,
                    data=data,
                    vapid_private_key=self._vapid_keys["private_key"],
                    vapid_claims={"sub": "mailto:nanobot@localhost"},
                )
            except WebPushException as e:
                if "410" in str(e) or "404" in str(e):
                    dead_endpoints.append(sub.get("endpoint", ""))
                else:
                    logger.debug(f"Push notification failed: {e}")
            except Exception as e:
                logger.debug(f"Push notification error: {e}")

        # Clean up expired subscriptions
        for ep in dead_endpoints:
            self._remove_subscription(ep)

    async def start(self) -> None:
        """Start the WebSocket server."""
        import websockets

        self._running = True
        host = self.config.host
        port = self.config.port

        if self.event_bus:
            self.event_bus.subscribe(self._on_agent_event)

        self._server = await websockets.serve(self._handler, host, port)
        logger.info(f"API channel listening on ws://{host}:{port}")

        await self._server.wait_closed()

    async def _on_agent_event(self, event: "AgentEvent") -> None:
        """Broadcast an agent event to all connected WebSocket clients."""
        # Send push notification on final response (non-blocking)
        if (event.category == "agent" and event.event == "thinking_finished"
                and self._push_subscriptions):
            asyncio.create_task(self._send_push_notification("Nanobot", "Response ready"))

        if not self._connections:
            return

        # Stream events get their own wire protocol messages
        # event.event is already "stream_start" / "stream_chunk" / "stream_end"
        if event.category == "stream":
            stream_type = event.event
            msg: dict[str, Any] = {"type": stream_type}
            if "id" in event.data:
                msg["id"] = event.data["id"]
            if "delta" in event.data:
                msg["delta"] = event.data["delta"]
            payload = json.dumps(msg)
        else:
            payload = json.dumps({
                "type": "event",
                "category": event.category,
                "event": event.event,
                "data": event.data,
            })
        dead: list[str] = []
        for conn_id, ws in list(self._connections.items()):
            try:
                await ws.send(payload)
            except Exception:
                dead.append(conn_id)
        for conn_id in dead:
            self._connections.pop(conn_id, None)

    async def stop(self) -> None:
        """Stop the WebSocket server and close all connections."""
        self._running = False

        if self.event_bus:
            self.event_bus.unsubscribe(self._on_agent_event)

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

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        """Reject URLs targeting private/reserved IP ranges."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return False
        except ValueError:
            pass  # domain name, not IP — OK
        return True

    async def _fetch_link_preview(self, url: str) -> dict[str, Any]:
        """Fetch Open Graph metadata for a URL. Results are cached."""
        if not self._is_safe_url(url):
            return {"url": url}

        now = time.monotonic()
        cached = _link_preview_cache.get(url)
        if cached and (now - cached[1]) < _LINK_PREVIEW_TTL:
            return cached[0]

        result: dict[str, Any] = {"url": url}
        try:
            async with httpx.AsyncClient(
                timeout=5, follow_redirects=True,
                headers={"User-Agent": "NanobotLinkPreview/1.0"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Open Graph tags
            for prop in ("og:title", "og:description", "og:image"):
                tag = soup.find("meta", attrs={"property": prop})
                if tag and tag.get("content"):
                    key = prop.split(":")[1]  # title, description, image
                    result[key] = tag["content"]

            # Fallback to <title>
            if "title" not in result:
                title_tag = soup.find("title")
                if title_tag and title_tag.string:
                    result["title"] = title_tag.string.strip()

            # Fallback description from meta name="description"
            if "description" not in result:
                desc_tag = soup.find("meta", attrs={"name": "description"})
                if desc_tag and desc_tag.get("content"):
                    result["description"] = desc_tag["content"]

            # Favicon
            parsed = urlparse(url)
            icon_tag = soup.find("link", rel=lambda v: v and "icon" in v)
            if icon_tag and icon_tag.get("href"):
                href = icon_tag["href"]
                if href.startswith("//"):
                    href = f"{parsed.scheme}:{href}"
                elif href.startswith("/"):
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                result["favicon"] = href
            else:
                result["favicon"] = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

        except Exception as e:
            logger.debug(f"Link preview failed for {url}: {e}")
            # Return whatever we have (at minimum just the url)

        # Evict expired entries if cache is full
        if len(_link_preview_cache) >= _LINK_PREVIEW_MAX:
            expired = [k for k, (_, ts) in _link_preview_cache.items()
                       if (now - ts) >= _LINK_PREVIEW_TTL]
            for k in expired:
                del _link_preview_cache[k]
            # If still full, drop oldest half
            if len(_link_preview_cache) >= _LINK_PREVIEW_MAX:
                sorted_keys = sorted(_link_preview_cache, key=lambda k: _link_preview_cache[k][1])
                for k in sorted_keys[:len(sorted_keys) // 2]:
                    del _link_preview_cache[k]

        _link_preview_cache[url] = (result, now)
        return result

    async def _process_message(self, ws, conn_id: str, raw: str) -> None:
        """Parse and route a single inbound message."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send(json.dumps({"type": "error", "content": "Invalid JSON"}))
            return

        msg_type = data.get("type")

        if msg_type == "link_preview":
            url = data.get("url", "")
            if url:
                result = await self._fetch_link_preview(url)
                payload = json.dumps({"type": "link_preview_result", **result})
                try:
                    await ws.send(payload)
                except Exception as e:
                    logger.debug(f"Failed to send link preview: {e}")
            return

        if msg_type == "push_vapid":
            keys = self._ensure_vapid_keys()
            payload = json.dumps({"type": "push_vapid_key", "key": keys["public_key"]})
            await ws.send(payload)
            return

        if msg_type == "push_subscribe":
            subscription = data.get("subscription")
            if subscription:
                self._add_subscription(subscription)
            return

        if msg_type == "push_unsubscribe":
            endpoint = data.get("endpoint", "")
            if endpoint:
                self._remove_subscription(endpoint)
            return

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
