
import ipaddress
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from clipforge.worker import create_job, get_job


app = FastAPI(
    title="ClipForge AI",
    description="Cloud-based AI video clipping API",
    version="0.4.0",
)


def validate_public_hostname(hostname: str) -> None:
    hostname = hostname.lower().rstrip(".")

    blocked_suffixes = (
        ".localhost",
        ".local",
        ".internal",
        ".home.arpa",
    )

    if (
        hostname == "localhost"
        or any(hostname.endswith(suffix) for suffix in blocked_suffixes)
        or "." not in hostname
    ):
        raise ValueError("Local network hostnames are not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return

    if not address.is_global:
        raise ValueError("Private or non-public IP addresses are not allowed")


class ClipRequest(BaseModel):
    video_url: HttpUrl
    duration: int = Field(default=45, ge=15, le=180)
    source: str = Field(default="auto")

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value):
        parsed = urlsplit(str(value))

        if parsed.scheme != "https":
            raise ValueError("Only HTTPS video URLs are accepted")

        if not parsed.hostname:
            raise ValueError("A valid video hostname is required")

        if parsed.username or parsed.password:
            raise ValueError("URLs containing credentials are not allowed")

        validate_public_hostname(parsed.hostname)

        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value):
        if value not in ("auto", "youtube", "direct"):
            raise ValueError("Source must be auto, youtube, or direct")
        return value

    @model_validator(mode="after")
    def detect_video_source(self):
        hostname = urlsplit(str(self.video_url)).hostname.lower()

        youtube_domains = ("youtube.com", "youtu.be")

        is_youtube = any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in youtube_domains
        )

        if self.source == "youtube" and not is_youtube:
            raise ValueError("A YouTube URL is required for this source")

        if self.source == "direct" and is_youtube:
            raise ValueError("Use the youtube source for YouTube links")

        if self.source == "auto":
            self.source = "youtube" if is_youtube else "direct"

        return self


@app.get("/")
def home():
    return {
        "message": "ClipForge AI cloud API is running",
        "version": "0.4.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/clips", status_code=202)
def create_clip(request: ClipRequest):
    try:
        job = create_job(
            video_url=str(request.video_url),
            source=request.source,
            duration=request.duration,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {
        "message": "Video job created",
        "job": job.model_dump(mode="json"),
    }


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"job": job.model_dump(mode="json")}
