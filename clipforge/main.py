from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, Field, field_validator
from urllib.parse import urlsplit

app = FastAPI(
    title="ClipForge AI",
    description="Cloud-based AI video clipping API",
    version="0.2.0"
)


class ClipRequest(BaseModel):
    video_url: HttpUrl
    duration: int = Field(default=45, ge=15, le=180)

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


@app.get("/")
def home():
    return {
        "message": "ClipForge AI cloud API is running",
        "version": "0.2.0"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/clips")
def create_clip(request: ClipRequest):
    return {
        "status": "validated",
        "video_url": str(request.video_url),
        "duration": request.duration,
        "message": "Video request validated. Cloud processing is not implemented yet."
    }
