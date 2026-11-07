from enum import Enum
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoJob(BaseModel):
    job_id: str
    video_url: str
    source: str
    duration: int = Field(default=45, ge=15, le=180)
    status: JobStatus = JobStatus.QUEUED
    result_url: str | None = None
    error: str | None = None


_jobs: dict[str, VideoJob] = {}
_active_job_id: str | None = None
_lock = Lock()


def create_job(video_url: str, source: str, duration: int) -> VideoJob:
    global _active_job_id

    with _lock:
        if _active_job_id is not None:
            active = _jobs.get(_active_job_id)

            if active and active.status in (
                JobStatus.QUEUED,
                JobStatus.PROCESSING,
            ):
                raise RuntimeError("A video job is already active")

        job = VideoJob(
            job_id=str(uuid4()),
            video_url=video_url,
            source=source,
            duration=duration,
        )

        _jobs[job.job_id] = job
        _active_job_id = job.job_id

        return job


def get_job(job_id: str) -> VideoJob | None:
    with _lock:
        return _jobs.get(job_id)


def process_video(job: VideoJob) -> VideoJob:
    raise NotImplementedError(
        "Video processing is not implemented yet."
    )
