"""Logic to detect highlights and score clips."""
from typing import List, Dict, Any
import numpy as np
import subprocess
import json
import tempfile

KEYWORDS = {"wow", "amazing", "crazy", "awesome", "unbelievable"}


def detect_highlights(transcript: List[Dict[str, Any]], video_path: str) -> List[Dict[str, Any]]:
    """Identify highlight-worthy moments based on transcript & audio volume spikes.

    Returns list of {start, end, text}
    """
    highlights = []
    for segment in transcript:
        text_lower = segment["text"].lower()
        if any(word in text_lower for word in KEYWORDS):
            highlights.append({"start": segment["start"], "end": segment["end"], "text": segment["text"].strip()})

    # TODO: Detect pauses > 1s & high volume spikes (basic placeholder)

    # Merge overlapping segments & limit to top 5
    highlights = sorted(highlights, key=lambda x: x["start"])
    merged = []
    for h in highlights:
        if merged and h["start"] - merged[-1]["end"] < 0.5:
            merged[-1]["end"] = max(merged[-1]["end"], h["end"])
            merged[-1]["text"] += " " + h["text"]
        else:
            merged.append(h)
    return merged[:5]


def score_clip(clip_path: str) -> int:
    """Very naive virality scoring based on duration and keyword count."""
    # Get duration via ffprobe
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        clip_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(r.stdout)
    duration = float(info["format"]["duration"])

    # Simple heuristic: shorter than 60s gets higher score
    base = max(0, 60 - duration) / 60 * 50

    # Placeholder randomness for now
    score = int(base + np.random.randint(20, 50))
    return min(score, 100)
