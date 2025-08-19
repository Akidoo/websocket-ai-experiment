from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import ollama
import asyncio

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat with AI</title>
    </head>
    <body>
        <h1>AI Chat</h1>
       <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'></ul>
        <script>
            const urlParams = new URLSearchParams(window.location.search);
            var client_id = urlParams.get("id");

            if (!client_id) {
                client_id = Date.now();
            }
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);

            var currentAIMessage = null;

            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');


                if (event.data.startsWith("You:")) {
                    var message = document.createElement('li');
                    message.textContent = event.data;
                    messages.appendChild(message);
                    currentAIMessage = null;
                }
                else {
                    if (!currentAIMessage) {
                        currentAIMessage = document.createElement('li');
                        
                        messages.appendChild(currentAIMessage);
                    }
                    currentAIMessage.textContent += event.data;
                }
            };

            function sendMessage(event) {
                var input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""

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
    return HTMLResponse(html)

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

            await manager.send_message("AI: ", client_id)  # prefix
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