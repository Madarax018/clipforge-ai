from fastapi.testclient import TestClient
from clipforge.main import app
from clipforge.worker import JobStatus, VideoJob

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "0.3.0"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_valid_clip_request():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4",
        "duration": 45
    })
    assert response.status_code == 200
    assert response.json()["status"] == "validated"
    assert response.json()["duration"] == 45
    assert response.json()["source"] == "direct"


def test_reject_http_url():
    response = client.post("/clips", json={
        "video_url": "http://example.com/video.mp4",
        "duration": 45
    })
    assert response.status_code == 422


def test_reject_short_duration():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4",
        "duration": 10
    })
    assert response.status_code == 422


def test_reject_long_duration():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4",
        "duration": 200
    })
    assert response.status_code == 422


def test_detect_youtube_source():
    response = client.post("/clips", json={
        "video_url": "https://www.youtube.com/watch?v=abc123"
    })
    assert response.status_code == 200
    assert response.json()["source"] == "youtube"


def test_detect_direct_source():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4"
    })
    assert response.status_code == 200
    assert response.json()["source"] == "direct"


def test_accept_explicit_youtube_source():
    response = client.post("/clips", json={
        "video_url": "https://youtu.be/abc123",
        "source": "youtube"
    })
    assert response.status_code == 200
    assert response.json()["source"] == "youtube"


def test_reject_youtube_url_as_direct_source():
    response = client.post("/clips", json={
        "video_url": "https://youtube.com/watch?v=abc123",
        "source": "direct"
    })
    assert response.status_code == 422


def test_video_job_defaults():
    job = VideoJob(
        job_id="test-001",
        video_url="https://example.com/video.mp4",
        source="direct"
    )
    assert job.status == JobStatus.QUEUED
    assert job.duration == 45
    assert job.result_url is None
    assert job.error is None


def test_video_job_custom_duration():
    job = VideoJob(
        job_id="test-002",
        video_url="https://youtube.com/watch?v=abc123",
        source="youtube",
        duration=60
    )
    assert job.duration == 60
    assert job.source == "youtube"


def test_video_job_status_values():
    assert JobStatus.QUEUED == "queued"
    assert JobStatus.PROCESSING == "processing"
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"
