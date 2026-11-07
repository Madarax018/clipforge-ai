from fastapi.testclient import TestClient
from clipforge.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "0.2.0"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_valid_clip_request():
    response = client.post(
        "/clips",
        json={
            "video_url": "https://example.com/video.mp4",
            "duration": 45
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "validated"
    assert response.json()["duration"] == 45


def test_reject_http_url():
    response = client.post(
        "/clips",
        json={
            "video_url": "http://example.com/video.mp4",
            "duration": 45
        }
    )

    assert response.status_code == 422


def test_reject_short_duration():
    response = client.post(
        "/clips",
        json={
            "video_url": "https://example.com/video.mp4",
            "duration": 10
        }
    )

    assert response.status_code == 422


def test_reject_long_duration():
    response = client.post(
        "/clips",
        json={
            "video_url": "https://example.com/video.mp4",
            "duration": 200
        }
    )

    assert response.status_code == 422
