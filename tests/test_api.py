
from fastapi.testclient import TestClient
from clipforge.main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200

def test_health():
    response = client.get("/health")
    assert response.json()["status"] == "healthy"

def test_create_clip():
    response = client.post(
        "/clips",
        json={
            "video_url": "https://example.com/video.mp4",
            "duration": 45
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "received"
