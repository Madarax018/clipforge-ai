from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

app = FastAPI(
    title="ClipForge AI",
    description="Cloud-based AI video clipping API",
    version="0.3.0",
)


class ClipRequest(BaseModel):
    video_url: HttpUrl
    duration: int = Field(default=45, ge=15, le=180)
    source: Literal["auto", "youtube", "direct"] = "auto"

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

        return value

    @model_validator(mode="after")
    def detect_video_source(self):
        hostname = urlsplit(str(self.video_url)).hostname.lower()

        youtube_domains = (
            "youtube.com",
            "youtu.be",
        )

        is_youtube = any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in youtube_domains
        )

        if self.source == "youtube" and not is_youtube:
            raise ValueError("A YouTube URL is required for this source")

        if self.source == "direct" and is_youtube:
            raise ValueError(
                "Use the youtube source for YouTube links"
            )

        if self.source == "auto":
            self.source = "youtube" if is_youtube else "direct"

        return self


@app.get("/")
def home():
    return {
        "message": "ClipForge AI cloud API is running",
        "version": "0.3.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/clips")
def create_clip(request: ClipRequest):
    return {
        "status": "validated",
        "video_url": str(request.video_url),
        "source": request.source,
        "duration": request.duration,
        "message": (
            "Video request validated. "
            "Cloud processing is not implemented yet."
        ),
    }
