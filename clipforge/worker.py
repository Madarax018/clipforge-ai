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


def update_job_status(
    job_id: str,
    status: JobStatus,
    result_url: str | None = None,
    error: str | None = None,
) -> VideoJob:
    global _active_job_id

    with _lock:
        job = _jobs.get(job_id)

        if job is None:
            raise KeyError("Job not found")

        allowed_transitions = {
            JobStatus.QUEUED: [JobStatus.PROCESSING],
            JobStatus.PROCESSING: [
                JobStatus.COMPLETED,
                JobStatus.FAILED,
            ],
        }

        if status not in allowed_transitions.get(job.status, []):
            raise ValueError("Invalid job status transition")

        if status == JobStatus.COMPLETED and not result_url:
            raise ValueError("Completed jobs require a result URL")

        if status == JobStatus.FAILED and not error:
            raise ValueError("Failed jobs require an error message")

        updated = job.model_copy(
            update={
                "status": status,
                "result_url": result_url,
                "error": error,
            }
        )

        _jobs[job_id] = updated

        if status in (JobStatus.COMPLETED, JobStatus.FAILED):
            if _active_job_id == job_id:
                _active_job_id = None

        return updated


def process_video(job: VideoJob) -> VideoJob:
    raise NotImplementedError(
        "Video processing is not implemented yet."
    )
