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
