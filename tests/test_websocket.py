import json
from starlette.testclient import TestClient
from app.main import app


def test_websocket_invalid_json():
    with TestClient(app) as client:
        with client.websocket_connect('/ws') as websocket:
            websocket.send_text('not json')
            data = json.loads(websocket.receive_text())
            assert data['type'] == 'error'
            assert 'Invalid JSON' in data['content']


def test_websocket_chat_message(monkeypatch):
    class DummyAgent:
        def chat(self, msg):
            return 'pong'

    monkeypatch.setattr('app.main.DockerManager', lambda: None)
    monkeypatch.setattr('app.main.AIAgent', lambda dm, api_key: DummyAgent())
    with TestClient(app) as client:
        with client.websocket_connect('/ws') as websocket:
            websocket.send_text(json.dumps({'type': 'chat_message', 'content': 'ping'}))
            data = json.loads(websocket.receive_text())
            assert data['type'] == 'chat_message'
            assert data['content'] == 'pong'
