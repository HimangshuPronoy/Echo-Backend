"""Whisper transcription utilities"""
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any

import whisper

MODEL_NAME = "tiny"  # Default; override via env var WHISPER_MODEL

model = whisper.load_model(MODEL_NAME)


def transcribe_audio(video_path: str) -> List[Dict[str, Any]]:
    """Extract audio from video and run Whisper to produce transcript segments.

    Returns a list of segments: [{"start": float, "end": float, "text": str}]
    """
    # Extract audio to wav using ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_audio:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            tmp_audio.name,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # Run Whisper
        result = model.transcribe(tmp_audio.name, word_timestamps=False)
    return result["segments"]
