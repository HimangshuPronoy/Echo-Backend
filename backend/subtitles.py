"""Subtitle utilities."""
from typing import List, Dict, Any


def generate_srt(segments: List[Dict[str, Any]], srt_path: str):
    """Write segments to SRT file."""
    def format_timestamp(seconds: float) -> str:
        millis = int((seconds - int(seconds)) * 1000)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02},{millis:03}"

    with open(srt_path, "w") as f:
        for idx, seg in enumerate(segments, start=1):
            start_ts = format_timestamp(seg["start"])
            end_ts = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"{idx}\n{start_ts} --> {end_ts}\n{text}\n\n")
