import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.db.session import get_db
from app.core.utils import get_current_user, authenticate
from app.controllers.chat_controller import ChatController
from app.services.socket_registry import ConversationBridge

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

@router.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    try:
        access_token = await authenticate(websocket)
        buyer_cred = await get_current_user(websocket)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await websocket.close(code=1008, reason=str(e))
        return

    await websocket.accept()
    user_id = buyer_cred.get("id")
    is_admin = buyer_cred.get("is_admin", False)

    bridge = ConversationBridge(websocket)

    try:
        async for db in get_db():
            while True:
                data = await websocket.receive_json()
                conversation_id = await ChatController.handle_message(
                    websocket=websocket,
                    data=data,
                    db=db,
                    user_id=user_id,
                    access_token=access_token,
                    is_admin=is_admin,
                )
                if conversation_id:
                    await bridge.ensure_subscribed(conversation_id) # this subs to the conversation id channel
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
    finally:
        await bridge.close()