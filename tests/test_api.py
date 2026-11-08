import pytest
from fastapi.testclient import TestClient

from clipforge.main import app
from clipforge import worker
from clipforge.worker import (
    JobStatus,
    VideoJob,
    create_job,
    update_job_status,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_jobs():
    with worker._lock:
        worker._jobs.clear()
        worker._active_job_id = None


# API tests

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "0.4.0"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_clip_job():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4",
        "duration": 45
    })

    assert response.status_code == 202
    data = response.json()["job"]
    assert data["status"] == "queued"
    assert data["source"] == "direct"
    assert data["duration"] == 45
    assert data["job_id"]


def test_detect_youtube_source():
    response = client.post("/clips", json={
        "video_url": "https://www.youtube.com/watch?v=abc123"
    })

    assert response.status_code == 202
    assert response.json()["job"]["source"] == "youtube"


def test_detect_direct_source():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4"
    })

    assert response.status_code == 202
    assert response.json()["job"]["source"] == "direct"


def test_reject_http_url():
    response = client.post("/clips", json={
        "video_url": "http://example.com/video.mp4"
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


def test_reject_invalid_source():
    response = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4",
        "source": "unknown"
    })
    assert response.status_code == 422


def test_reject_youtube_as_direct_source():
    response = client.post("/clips", json={
        "video_url": "https://youtube.com/watch?v=abc123",
        "source": "direct"
    })
    assert response.status_code == 422


def test_get_job_status():
    created = client.post("/clips", json={
        "video_url": "https://example.com/video.mp4"
    })

    job_id = created.json()["job"]["job_id"]
    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["job"]["job_id"] == job_id
    assert response.json()["job"]["status"] == "queued"


def test_unknown_job_returns_404():
    response = client.get("/jobs/not-a-real-job")
    assert response.status_code == 404


def test_only_one_active_job_allowed():
    first = client.post("/clips", json={
        "video_url": "https://example.com/first.mp4"
    })

    second = client.post("/clips", json={
        "video_url": "https://example.com/second.mp4"
    })

    assert first.status_code == 202
    assert second.status_code == 409


# Video job model tests

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


# Worker lifecycle tests

def test_job_moves_to_processing():
    job = create_job(
        "https://example.com/video.mp4",
        "direct",
        45,
    )

    updated = update_job_status(
        job.job_id,
        JobStatus.PROCESSING,
    )

    assert updated.status == JobStatus.PROCESSING


def test_job_moves_to_completed():
    job = create_job(
        "https://example.com/video.mp4",
        "direct",
        45,
    )

    update_job_status(job.job_id, JobStatus.PROCESSING)

    updated = update_job_status(
        job.job_id,
        JobStatus.COMPLETED,
        result_url="https://example.com/result.mp4",
    )

    assert updated.status == JobStatus.COMPLETED
    assert updated.result_url == "https://example.com/result.mp4"


def test_job_moves_to_failed():
    job = create_job(
        "https://example.com/video.mp4",
        "direct",
        45,
    )

    update_job_status(job.job_id, JobStatus.PROCESSING)

    updated = update_job_status(
        job.job_id,
        JobStatus.FAILED,
        error="Test processing failure",
    )

    assert updated.status == JobStatus.FAILED
    assert updated.error == "Test processing failure"


def test_reject_invalid_job_transition():
    job = create_job(
        "https://example.com/video.mp4",
        "direct",
        45,
    )

    with pytest.raises(ValueError):
        update_job_status(job.job_id, JobStatus.COMPLETED)


def test_completed_job_requires_result_url():
    job = create_job(
        "https://example.com/video.mp4",
        "direct",
        45,
    )

    update_job_status(job.job_id, JobStatus.PROCESSING)

    with pytest.raises(ValueError):
        update_job_status(job.job_id, JobStatus.COMPLETED)


def test_failed_job_requires_error():
    job = create_job(
        "https://example.com/video.mp4",
        "direct",
        45,
    )

    update_job_status(job.job_id, JobStatus.PROCESSING)

    with pytest.raises(ValueError):
        update_job_status(job.job_id, JobStatus.FAILED)

def test_new_job_allowed_after_completion():
    first = create_job(
        "https://example.com/first.mp4",
        "direct",
        45,
    )

    update_job_status(first.job_id, JobStatus.PROCESSING)
    update_job_status(
        first.job_id,
        JobStatus.COMPLETED,
        result_url="https://example.com/result.mp4",
    )

    second = create_job(
        "https://example.com/second.mp4",
        "direct",
        45,
    )

    assert second.status == JobStatus.QUEUED


def test_new_job_allowed_after_failure():
    first = create_job(
        "https://example.com/first.mp4",
        "direct",
        45,
    )

    update_job_status(first.job_id, JobStatus.PROCESSING)
    update_job_status(
        first.job_id,
        JobStatus.FAILED,
        error="Test failure",
    )

    second = create_job(
        "https://example.com/second.mp4",
        "direct",
        45,
    )

    assert second.status == JobStatus.QUEUED


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost/video.mp4",
        "https://127.0.0.1/video.mp4",
        "https://192.168.1.10/video.mp4",
        "https://10.0.0.5/video.mp4",
        "https://router.local/video.mp4",
    ],
)
def test_reject_private_or_local_hosts(url):
    response = client.post(
        "/clips",
        json={"video_url": url},
    )

    assert response.status_code == 422
