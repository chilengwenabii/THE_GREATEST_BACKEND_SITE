"""
Live Calling Router: WebSocket Signaling for WebRTC
"""
import json
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from jose import JWTError, jwt
from decouple import config

from auth import SECRET_KEY, ALGORITHM
from database import SessionLocal
from models import FamilyMemberORM

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# =============================================================================
# Connection Manager
# =============================================================================

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: WebSocket}
        # Assuming one connection per user for simplicity.
        # If multiple tabs, we might need a list, but for calling, usually one active device is best.
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        # If user already has a connection, we might want to close the old one or allow multiple.
        # For now, we'll overwrite or just store it. 
        # Simpler to just overwrite for "single active device" policy or handle list.
        # Let's handle list to be safe, but typically we route to all user's devices.
        # Re-evaluating: implementation plan said "mapped to user_id". 
        # Let's just store the socket. If we need multiple, we'll change to list later.
        if user_id in self.active_connections:
            # Optionally close old connection
             # await self.active_connections[user_id].close(code=status.WS_1000_NORMAL_CLOSURE)
             pass
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to signaling.")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from signaling.")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Clean up if dead
                # self.disconnect(user_id) # Be careful removing mid-loop

manager = ConnectionManager()

# =============================================================================
# Auth Helper
# =============================================================================

async def get_current_user_ws(
    token: Optional[str] = Query(None)
) -> Optional[int]:
    """
    Validate JWT token from query parameter.
    Returns user_id if valid, None otherwise.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    # We need the User ID. Query DB.
    db = SessionLocal()
    try:
        user = db.query(FamilyMemberORM).filter(FamilyMemberORM.username == username).first()
        if user:
            return user.id
    finally:
        db.close()
    
    return None

# =============================================================================
# WebSocket Endpoint
# =============================================================================

@router.websocket("/ws/signaling")
async def websocket_signaling(workspace: WebSocket, token: Optional[str] = Query(None)):
    """
    Signaling endpoint for WebRTC.
    """
    user_id = await get_current_user_ws(token)
    
    if not user_id:
        # Reject connection
        await workspace.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(workspace, user_id)

    try:
        while True:
            data = await workspace.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                target_user_id = message.get("targetUserId")

                # Basic logging
                # logger.info(f"Received {msg_type} from {user_id} to {target_user_id}")

                if target_user_id:
                    # Enforce that target_user_id is int
                    target_user_id = int(target_user_id)
                    
                    # Prepare payload to forward
                    # We inject the sender's generic info so the receiver knows who is calling
                    forward_payload = {
                        "type": msg_type,
                        "senderUserId": user_id,
                        # Pass through other fields
                        "sdp": message.get("sdp"),
                        "candidate": message.get("candidate"),
                        "payload": message.get("payload") # generic payload if needed
                    }
                    
                    # Send to target
                    if target_user_id in manager.active_connections:
                        await manager.send_personal_message(forward_payload, target_user_id)
                    else:
                        # Target not online
                        # Optionally notify sender
                        await manager.send_personal_message({
                            "type": "error",
                            "message": "User is not online"
                        }, user_id)
                        
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket fatal error: {e}")
        manager.disconnect(user_id)
