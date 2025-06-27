# EchoCut Pro Backend

FastAPI backend that ingests a video, detects highlight moments, generates short clips with burned-in subtitles & a watermark, and scores each clip for virality.

### Features
* `POST /upload` – Upload `.mp4` / `.mov` video and receive a `job_id`.
* `GET /status/{job_id}` – Poll processing status & retrieve clip metadata once done.
* Static serving of original videos (`/videos/{job_id}.mp4`) and processed clips (`/clips/{job_id}/clipX.mp4`).
* Local Whisper (`tiny` model) transcription; no external API keys required.
* Heuristic highlight detection (emotion keywords, etc.).
* FFmpeg-based clip extraction, subtitle burn-in, and watermark overlay.
* Docker-ready with FFmpeg & Python deps pre-installed.

### Quick Start (Locally)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for Swagger UI.

### Docker
```bash
docker build -t echocut-pro .
docker run -p 8000:8000 echocut-pro
```

### Railway Deployment
1. Push this repo to GitHub.
2. In Railway, **New Project → Deploy from GitHub**.
3. Add environment variables if desired (e.g., `BRAND_LOGO_URL`).
4. Railway will detect the Dockerfile and build.
5. Once running, open `/docs` for the interactive API.

---
© 2025 EchoCut Pro
