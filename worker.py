from enum import Enum
from pydantic import BaseModel


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoJob(BaseModel):
    job_id: str
    video_url: str
    source: str
    duration: int = 45
    status: JobStatus = JobStatus.QUEUED
    result_url: str | None = None
    error: str | None = None


def process_video(job: VideoJob) -> VideoJob:
    """
    Processing entry point.

    Actual video downloading, transcription and
    rendering will be implemented in later stages.
    """
    raise NotImplementedError(
        "Video processing worker is not implemented yet."
    )
