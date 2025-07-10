from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_static_files_served():
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "body" in response.text
