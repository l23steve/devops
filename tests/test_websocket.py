import json
from starlette.testclient import TestClient
from app.main import app


def test_websocket_invalid_json():
    client = TestClient(app)
    with client.websocket_connect('/ws') as websocket:
        websocket.send_text('not json')
        data = json.loads(websocket.receive_text())
        assert data['type'] == 'error'
        assert 'Invalid JSON' in data['content']


def test_websocket_streams_responses(monkeypatch):
    class DummyAgent:
        def chat(self, message, stream_callback=None):
            if stream_callback:
                stream_callback('partial')
            import time
            time.sleep(0.01)
            return 'done'

    monkeypatch.setattr('app.main.ai_agent', DummyAgent())

    client = TestClient(app)
    with client.websocket_connect('/ws') as websocket:
        websocket.send_text(json.dumps({'type': 'chat_message', 'content': 'hi'}))
        messages = [json.loads(websocket.receive_text()) for _ in range(2)]

        types = {m['type'] for m in messages}
        assert 'terminal_data' in types
        assert 'chat_message' in types

        term_msg = next(m for m in messages if m['type'] == 'terminal_data')
        chat_msg = next(m for m in messages if m['type'] == 'chat_message')

        assert term_msg['content'] == 'partial'
        assert chat_msg['content'] == 'done'
