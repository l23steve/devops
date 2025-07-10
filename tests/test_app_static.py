from starlette.testclient import TestClient
from app.main import app


def test_index_served():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')


def test_static_files_served():
    client = TestClient(app)
    response = client.get('/static/style.css')
    assert response.status_code == 200
    assert 'text/css' in response.headers.get('content-type', '')
    assert len(response.text) > 0
