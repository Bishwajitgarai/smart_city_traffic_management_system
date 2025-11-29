from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.traffic import TrafficLight
from app.core.traffic_logic import TrafficController
import json
from typing import List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            # Echo or handle client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_state_update(light_id: int, state: dict):
    """Helper function to broadcast state updates"""
    await manager.broadcast({
        "type": "state_update",
        "light_id": light_id,
        "state": state
    })

async def broadcast_batch_update(updates: list):
    """Helper function to broadcast multiple state updates"""
    await manager.broadcast({
        "type": "batch_state_update",
        "updates": updates
    })
