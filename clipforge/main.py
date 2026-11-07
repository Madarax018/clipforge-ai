
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl, Field

app = FastAPI(
    title="ClipForge AI",
    description="AI-powered video clipping API",
    version="0.1.0"
)

class ClipRequest(BaseModel):
    video_url: HttpUrl
    duration: int = Field(default=45, ge=15, le=180)

@app.get("/")
def home():
    return {"message": "ClipForge AI is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/clips")
def create_clip(request: ClipRequest):
    return {
        "status": "received",
        "video_url": str(request.video_url),
        "duration": request.duration,
        "message": "Clip processing is not implemented yet"
    }
