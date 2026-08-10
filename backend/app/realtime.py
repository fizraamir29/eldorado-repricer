"""
Real-time layer.

Each logged-in dashboard opens one WebSocket connection (see routers/ws.py).
When the scheduler changes a price, finds an error, or sends a follow-up
message, it calls `manager.send_to_user(...)` here, which pushes a JSON
event straight to that user's open tab(s) — no polling needed on the frontend.

If a user has no open connection right now, the event is simply not sent
live; it's still saved to the database (price_history / notifications) so
it shows up next time they open the dashboard.
"""
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger("realtime")


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[user_id].add(websocket)
        logger.info("WebSocket connected for user %s (total: %d)", user_id, len(self._connections[user_id]))

    def disconnect(self, user_id: str, websocket: WebSocket):
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            del self._connections[user_id]

    async def send_to_user(self, user_id: str, event: dict):
        """Fire-and-forget push. Dead sockets are dropped silently."""
        dead = []
        for ws in self._connections.get(user_id, set()):
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)


manager = ConnectionManager()
