from fastapi import websockets, WebSocketDisconnect, WebSocketException, APIRouter
from app.controllers.websocket_controller import WebsocketController
app = APIRouter(prefix="/api/v1/ws")

@app.websocket("/chat")
async def ws_handler(ws: websockets):
    WebsocketController.ws_controller(ws)
    ...