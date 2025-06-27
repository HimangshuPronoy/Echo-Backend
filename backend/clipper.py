"""Clip extraction and post-processing utilities using ffmpeg."""
from typing import List, Dict
import os
import subprocess


def create_clips(video_path: str, highlights: List[Dict], output_dir: str) -> List[str]:
    """Extract highlight segments into separate mp4 files.

    Returns list of raw clip paths.
    """
    clip_paths = []
    for idx, h in enumerate(highlights, start=1):
        start = h["start"]
        duration = h["end"] - h["start"]
        output_path = os.path.join(output_dir, f"raw_clip{idx}.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clip_paths.append(output_path)
    return clip_paths


def burn_subtitles_and_watermark(input_clip: str, srt_path: str, logo_path: str, output_path: str):
    """Burn subtitles and watermark onto a clip using ffmpeg drawtext & overlay."""
    # Build drawtext filter
    filters = []
    if os.path.isfile(srt_path):
        filters.append(f"subtitles='{srt_path}':force_style='FontSize=24'" )

    if os.path.isfile(logo_path):
        filters.append(f"movie={logo_path}[wm];[in][wm]overlay=W-w-10:H-h-10[out]")

    filter_chain = ",".join(filters) if filters else None

    cmd = ["ffmpeg", "-y", "-i", input_clip]
    if filter_chain:
        cmd += ["-vf", filter_chain]
    cmd += ["-c:v", "libx264", "-c:a", "aac", output_path]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
