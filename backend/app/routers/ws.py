"""
WebSocket endpoint for live dashboard updates.

Browsers can't attach an Authorization header to a native WebSocket
handshake, so the JWT is passed as a query parameter instead:

    ws://.../ws?token=<jwt>

This is standard practice for browser WebSockets — just make sure the
connection always runs over wss:// (TLS) in production so the token in the
URL isn't sent in plaintext.
"""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.security import decode_access_token
from app.realtime import manager

router = APIRouter(tags=["realtime"])
logger = logging.getLogger("ws")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        user_id = decode_access_token(token)
    except Exception:
        await websocket.close(code=4401)  # custom close code = unauthorized
        return

    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            await websocket.close(code=4401)
            return

    await manager.connect(user_id, websocket)
    try:
        while True:
            # We don't expect the client to send anything meaningful, but we
            # still need to await recv() to detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
