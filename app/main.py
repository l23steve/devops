import json
import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .docker_tools import DockerManager
from .ai_agent import AIAgent
from dotenv import load_dotenv
from app.internet_tools import WebSearchTool

load_dotenv()

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend")),
    name="static",
)

docker_manager = None
ai_agent = None

@app.on_event("startup")
def startup_event():
    global docker_manager, ai_agent
    api_key = os.getenv("OPENAI_KEY", "test")
    try:
        docker_manager = DockerManager()
        internet_tools = WebSearchTool(api_key=api_key)
    except Exception as exc:
        print(f"Failed to start docker container: {exc}")
        docker_manager = None
        internet_tools = None
    ai_agent = AIAgent(docker_manager, internet_tools, api_key)

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
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "content": "Invalid JSON"}))
                continue
            if msg.get("type") == "chat_message":
                user_msg = msg.get("content", "")
                print(f"Received message: {user_msg}")

                loop = asyncio.get_running_loop()

                def stream_cb(text: str):
                    loop.create_task(
                        websocket.send_text(
                            json.dumps({"type": "terminal_data", "content": text})
                        )
                    )

                ai_response = await asyncio.to_thread(
                    ai_agent.chat, user_msg, stream_callback=stream_cb
                )
                await websocket.send_text(
                    json.dumps({"type": "chat_message", "content": ai_response})
                )
    except WebSocketDisconnect as wsd:
        print(f"WebSocket disconnected: {wsd}")
