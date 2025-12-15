"""
WebSocket connection manager for real-time progress updates.
"""

import asyncio
from typing import List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for broadcasting updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


async def broadcast_progress(
    manager: ConnectionManager,
    step: int,
    total_steps: int,
    elapsed: float,
    status: str = "generating",
    image_url: Optional[str] = None,
    error: Optional[str] = None,
    generation_id: Optional[str] = None
):
    """
    Broadcast generation progress to all connected clients.

    Args:
        manager: ConnectionManager instance
        step: Current step number
        total_steps: Total number of steps
        elapsed: Elapsed time in seconds
        status: Current status ("generating", "complete", "error")
        image_url: URL of generated image (for complete status)
        error: Error message (for error status)
        generation_id: ID of the current generation
    """
    percentage = (step / total_steps) * 100 if total_steps > 0 else 0

    # Calculate ETA
    if step > 0:
        avg_time_per_step = elapsed / step
        remaining_steps = total_steps - step
        eta_seconds = avg_time_per_step * remaining_steps
    else:
        eta_seconds = 0

    message = {
        "type": "progress" if status == "generating" else status,
        "generation_id": generation_id,
        "data": {
            "step": step,
            "total_steps": total_steps,
            "percentage": round(percentage, 2),
            "eta_seconds": round(eta_seconds, 1),
            "elapsed_seconds": round(elapsed, 1),
            "status": status
        }
    }

    if status == "complete" and image_url:
        message["data"]["image_url"] = image_url

    if status == "error" and error:
        message["error"] = {
            "code": "GENERATION_FAILED",
            "message": error
        }

    await manager.broadcast(message)


async def broadcast_session_update(
    manager: ConnectionManager,
    generation_count: int,
    current_image_id: Optional[str] = None
):
    """
    Broadcast session update to all connected clients.

    Args:
        manager: ConnectionManager instance
        generation_count: Total number of generations in session
        current_image_id: ID of the current image
    """
    message = {
        "type": "session_update",
        "data": {
            "generation_count": generation_count,
            "current_image_id": current_image_id
        }
    }

    await manager.broadcast(message)
