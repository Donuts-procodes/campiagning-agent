import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.core.database import get_redis_client
from src.dependencies.graph import get_graph
from src.services.campaign_service import CampaignService

ws_router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, thread_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if thread_id not in self._connections:
            self._connections[thread_id] = []
        self._connections[thread_id].append(websocket)

    def disconnect(self, thread_id: str, websocket: WebSocket) -> None:
        if thread_id in self._connections:
            self._connections[thread_id].remove(websocket)
            if not self._connections[thread_id]:
                del self._connections[thread_id]

manager = ConnectionManager()

@ws_router.websocket("/{thread_id}")
async def campaign_ws(
    websocket: WebSocket, 
    thread_id: str, 
    api_key: str | None = None,
    graph: Any = Depends(get_graph)
) -> None:
    from src.core.config import settings
    # For websockets, we typically pass tokens in query params or initial message.
    # We will enforce API key via query parameter: ?api_key=XYZ
    if api_key != settings.API_KEY:
        await websocket.close(code=1008)
        return

    await manager.connect(thread_id, websocket)
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    channel = f"campaign_updates:{thread_id}"
    await pubsub.subscribe(channel)
    
    async def send_current_state():
        state_data = await CampaignService.get_state(thread_id, graph)
        ws_data = {
            "current_node": state_data.get("current_node", "unknown"),
            "next_nodes": state_data.get("next_nodes", []),
            "verification": state_data.get("verification"),
            "hitl": state_data.get("hitl"),
            "execution": state_data.get("execution"),
            "revision_count": state_data.get("revision_count", 0),
            "error": state_data.get("error"),
        }
        await websocket.send_json({"type": "state_update", "data": ws_data})

    try:
        # Send initial state
        await send_current_state()

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("data") is not None:
                try:
                    data = json.loads(message["data"])
                    if data.get("status") == "error":
                        await websocket.send_json({"type": "error", "message": data.get("message")})
                    else:
                        await send_current_state()
                except Exception as e:
                    logger.error(f"Error parsing redis message: {e}")
            
            # Receive empty pings to keep connection alive and detect client disconnects
            try:
                # Use wait_for to not block the pubsub loop indefinitely
                client_msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except TimeoutError:
                pass

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"WebSocket error for {thread_id}: {exc}")
    finally:
        await pubsub.unsubscribe(channel)
        manager.disconnect(thread_id, websocket)
