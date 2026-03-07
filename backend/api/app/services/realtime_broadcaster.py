"""Realtime websocket connection manager."""

import logging
from typing import Set

from fastapi import WebSocket

log = logging.getLogger(__name__)


class AlertConnectionManager:
    """Tracks and broadcasts to active dashboard websocket clients."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        log.info("WebSocket client connected (%d active)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        log.info("WebSocket client disconnected (%d active)", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        dead_connections = []
        for connection in list(self._connections):
            try:
                await connection.send_json(message)
            except Exception:
                log.warning("WebSocket send failed, removing dead connection")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


alert_connection_manager = AlertConnectionManager()