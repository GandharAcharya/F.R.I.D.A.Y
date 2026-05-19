from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import json

app = FastAPI(title="F.R.I.D.A.Y. Neural Router")

# CRITICAL: Opens the API so your React localhost can talk to it without security blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[NEURAL ROUTER]: UI Dashboard Connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("[NEURAL ROUTER]: UI Dashboard Disconnected.")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS ERROR]: Failed to send data - {str(e)}")

manager = ConnectionManager()

@app.websocket("/ws/cortex")
async def cortex_endpoint(websocket: WebSocket):
    """The main artery between F.R.I.D.A.Y.'s brain and the React UI."""
    await manager.connect(websocket)
    try:
        while True:
            # Listens for text commands you type into the UI
            data = await websocket.receive_text() 
            print(f"[DIRECTOR UI OVERRIDE]: {data}")
            # Here we will eventually route UI text back into the LLM
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def emit_cognitive_state(state_type: str, payload: dict):
    """Global function to push thoughts to the UI."""
    await manager.broadcast({"type": state_type, "payload": payload})

def start_neural_router():
    print("[NEURAL ROUTER]: WebSocket Engine Online. Listening on ws://localhost:8000/ws/cortex")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")