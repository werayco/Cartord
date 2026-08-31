import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.utils import get_current_buyer
from app.controllers.chat_controller import ChatController

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

@router.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    try:
        buyer_cred = await get_current_buyer(websocket)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await websocket.close(code=1008, reason=str(e))
        return
    
    await websocket.accept()
    
    async for db in get_db():
        try:
            while True:
                data = await websocket.receive_json()
                await ChatController.handle_message(
                    websocket=websocket,
                    data=data,
                    db=db,
                    user_id=buyer_cred.get("id")
                )
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {buyer_cred.get('id')}")
            break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close(code=1011, reason="Internal server error")
            break