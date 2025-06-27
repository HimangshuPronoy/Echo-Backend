from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
import shutil
import asyncio
import json
from typing import Dict, Any

from backend.transcriber import transcribe_audio
from backend.highlighter import detect_highlights, score_clip
from backend.clipper import create_clips, burn_subtitles_and_watermark
from backend.subtitles import generate_srt

app = FastAPI(title="EchoCut Pro API", version="1.0.0")

# CORS for browser clients
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: replace with specific domain(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
VIDEOS_DIR = os.path.join(PROJECT_ROOT, "videos")
CLIPS_DIR = os.path.join(PROJECT_ROOT, "clips")
JOBS_DIR = os.path.join(PROJECT_ROOT, "jobs")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
LOGO_PATH = os.getenv("BRAND_LOGO_URL", os.path.join(ASSETS_DIR, "logo.png"))

for directory in [VIDEOS_DIR, CLIPS_DIR, JOBS_DIR, ASSETS_DIR]:
    os.makedirs(directory, exist_ok=True)

# In-memory job tracker (simple; for production use persistent storage)
jobs: Dict[str, Dict[str, Any]] = {}


@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description=".mp4 or .mov video file"),
):
    """Accept a video file and start processing in the background."""
    if file.content_type not in ("video/mp4", "video/quicktime"):
        raise HTTPException(status_code=400, detail="Only .mp4 or .mov files are accepted.")

    job_id = str(uuid.uuid4())
    video_path = os.path.join(VIDEOS_DIR, f"{job_id}.mp4")

    # Save uploaded file
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Record initial status
    jobs[job_id] = {"status": "processing", "clips": []}

    # Kick off async processing
    background_tasks.add_task(process_job, job_id, video_path)
    return {"job_id": job_id}


async def process_job(job_id: str, video_path: str):
    """Pipeline: transcribe, highlight, clip, subtitle, watermark, score."""
    try:
        # 1. Transcription (Whisper tiny model)
        transcript = await asyncio.to_thread(transcribe_audio, video_path)

        # 2. Detect highlight-worthy moments
        highlights = detect_highlights(transcript, video_path)
        if not highlights:
            # Fallback: take first 15 seconds as a single clip
            highlights = [{"start": 0, "end": 15, "text": ""}]

        # 3. Generate SRT subtitles
        srt_path = os.path.join(JOBS_DIR, f"{job_id}.srt")
        generate_srt(transcript, srt_path)

        # 4. Clip extraction
        clip_dir = os.path.join(CLIPS_DIR, job_id)
        os.makedirs(clip_dir, exist_ok=True)
        raw_clips = create_clips(video_path, highlights, clip_dir)

        # 5. Burn subtitles + watermark + scoring
        results = []
        for idx, raw_clip in enumerate(raw_clips, start=1):
            final_clip_path = os.path.join(clip_dir, f"clip{idx}.mp4")
            burn_subtitles_and_watermark(
                raw_clip,
                srt_path,
                LOGO_PATH,
                output_path=final_clip_path,
            )
            score = score_clip(final_clip_path)
            results.append(
                {
                    "video_url": f"/clips/{job_id}/clip{idx}.mp4",
                    "subtitle": highlights[idx - 1].get("text", ""),
                    "score": score,
                }
            )

        # 6. Update job status & cache to disk
        jobs[job_id] = {"status": "done", "clips": results}
        with open(os.path.join(JOBS_DIR, f"{job_id}.json"), "w") as f:
            json.dump(jobs[job_id], f)

    except Exception as exc:
        jobs[job_id] = {"status": "error", "error": str(exc)}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Return processing status and clip metadata."""
    if job_id not in jobs:
        cache_path = os.path.join(JOBS_DIR, f"{job_id}.json")
        if os.path.isfile(cache_path):
            with open(cache_path) as f:
                jobs[job_id] = json.load(f)
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


# Serve original videos & processed clips as static files
audio_mp4 = "video/mp4"  # shorthand


@app.get("/videos/{video_name}")
async def serve_video(video_name: str):
    file_path = os.path.join(VIDEOS_DIR, video_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type=audio_mp4)


@app.get("/clips/{job_id}/{clip_name}")
async def serve_clip(job_id: str, clip_name: str):
    file_path = os.path.join(CLIPS_DIR, job_id, clip_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(file_path, media_type=audio_mp4)
