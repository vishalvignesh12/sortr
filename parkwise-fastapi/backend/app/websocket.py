import asyncio
import json
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from .cache import get_slot_status, set_slot_status
from . import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_session

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_types = {}  # Track what each connection is interested in

    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_types[websocket] = connection_type

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.connection_types:
            del self.connection_types[websocket]

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections[:]:  # Use slice to avoid modification during iteration
            try:
                await connection.send_text(json.dumps(message))
            except WebSocketDisconnect:
                # Handle disconnected clients
                self.disconnect(connection)

    async def send_to_type(self, message: dict, target_type: str):
        """Send message to specific type of client"""
        for connection in self.active_connections[:]:
            if self.connection_types.get(connection) == target_type:
                try:
                    await connection.send_text(json.dumps(message))
                except WebSocketDisconnect:
                    self.disconnect(connection)

manager = ConnectionManager()

# WebSocket endpoint for real-time updates
async def websocket_endpoint(websocket: WebSocket, connection_type: str = "general"):
    """
    WebSocket endpoint for real-time updates
    connection_type can be 'admin', 'user', 'dashboard', etc.
    """
    await manager.connect(websocket, connection_type)
    try:
        while True:
            # Listen for messages from client (if needed)
            try:
                data = await websocket.receive_text()
                # Process client messages if needed
                message_data = json.loads(data)
                
                # Example: client can request specific updates
                if message_data.get("action") == "subscribe":
                    # Handle subscription requests
                    pass
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Function to update clients about slot status changes
async def notify_slot_update(slot_id: str, new_status: dict):
    """Notify all connected clients about a slot status change"""
    message = {
        "type": "slot_update",
        "slot_id": slot_id,
        "status": new_status,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast(message)

# Function to update clients about booking changes
async def notify_booking_update(booking_id: str, user_id: str, status: str):
    """Notify relevant clients about a booking status change"""
    message = {
        "type": "booking_update", 
        "booking_id": booking_id,
        "user_id": user_id,
        "status": status,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Send to admin connections
    await manager.send_to_type(message, "admin")
    
    # Send to user-specific connections (if we track user connections)
    await manager.send_to_type(message, f"user_{user_id}")

# Function to update clients about system alerts
async def notify_system_alert(message: str, level: str = "info"):
    """Notify all connected clients about a system alert"""
    alert = {
        "type": "system_alert",
        "message": message,
        "level": level,  # 'info', 'warning', 'error'
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast(alert)