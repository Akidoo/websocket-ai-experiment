from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import ollama
import asyncio
from pathlib import Path
import uvicorn

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parents[2]  # this points to backend/
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self.histories: dict[int, list[dict]]= {}

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.histories[client_id] = []

    def disconnect(self, client_id: int):
        self.active_connections.pop(client_id, None)
        self.histories.pop(client_id, None)

    async def send_message(self, message: str, client_id: int):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)


manager = ConnectionManager()

@app.get("/")
async def get():
    return FileResponse(static_dir / "frontend.html")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()

            user_message = {"role": "user", "content": data}
            manager.histories[client_id].append(user_message)
        # await manager.send_personal_message(f"You: {data}", websocket)
            await manager.send_message(f"You: {data}", client_id)

        

            bot_response = ""
            stream = ollama.chat(
                model="phi3:mini",
                messages=manager.histories[client_id],
                stream=True
            )

            await manager.send_message("chungusAI: ", client_id)  # prefix
            for chunk in stream:
                content = chunk.message.content
                bot_response += content

                for ch in content:
                    await manager.send_message(ch, client_id)
                    await asyncio.sleep(0.02)
    
        
            bot_message = {"role": "assistant", "content": bot_response}
            manager.histories[client_id].append(bot_message)


    except WebSocketDisconnect:
        manager.disconnect(client_id)

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)
