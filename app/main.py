import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from .docker_tools import DockerManager
from .ai_agent import AIAgent

app = FastAPI()

docker_manager = None
ai_agent = None

@app.on_event("startup")
def startup_event():
    global docker_manager, ai_agent
    api_key = os.getenv("OPENROUTER_API_KEY", "test")
    try:
        docker_manager = DockerManager()
    except Exception as exc:
        print(f"Failed to start docker container: {exc}")
        docker_manager = None
    ai_agent = AIAgent(docker_manager, api_key)

@app.on_event("shutdown")
def shutdown_event():
    if docker_manager:
        docker_manager.stop()

@app.get("/")
async def get_index():
    with open(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")) as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "chat_message":
                user_msg = msg.get("content", "")
                ai_response = ai_agent.chat(user_msg)
                await websocket.send_text(json.dumps({"type": "chat_message", "content": ai_response}))
    except WebSocketDisconnect:
        pass
