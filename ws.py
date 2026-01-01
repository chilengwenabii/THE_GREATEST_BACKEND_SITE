import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WS-SERVER")

app = FastAPI(title="The Greatest WebSocket Server")

class ConnectionManager:
    def __init__(self):
        # Store active connections: {conversation_id: [WebSocket, ...]}
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: int):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        logger.info(f"New connection to channel {conversation_id}. Total: {len(self.active_connections[conversation_id])}")

    def disconnect(self, websocket: WebSocket, conversation_id: int):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]
            logger.info(f"Disconnected from channel {conversation_id}")

    async def broadcast(self, message: str, conversation_id: int):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to connection: {e}")

manager = ConnectionManager()

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int):
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            # We don't necessarily expect messages from client for now, 
            # but we keep the connection open and can handle incoming data if needed.
            data = await websocket.receive_text()
            # If we receive a message relay, we could handle it here, 
            # but usually messages are sent via REST API and broadcasted from there.
            # For now, just a heartbeat or echo.
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(f"WebSocket error in channel {conversation_id}: {e}")
        manager.disconnect(websocket, conversation_id)

@app.post("/broadcast/{conversation_id}")
async def broadcast_message(conversation_id: int, message: dict):
    """
    Internal endpoint to broadcast a message to all connected clients in a conversation.
    This would be called by the main API server when a new message is saved.
    """
    await manager.broadcast(json.dumps(message), conversation_id)
    return {"status": "broadcasted"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting WebSocket server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
