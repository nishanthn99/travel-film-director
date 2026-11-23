from pathlib import Path
import json
import subprocess


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def inspect_media(path: Path) -> dict:
    result = {
        "media_type": "video" if is_video(path) else "image",
        "size_bytes": path.stat().st_size,
        "duration_seconds": None,
        "width": None,
        "height": None,
        "metadata_available": False,
    }
    if not is_video(path):
        return result

    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=width,height", "-of", "json", str(path),
            ],
            capture_output=True, text=True, timeout=15, check=True,
        )
        payload = json.loads(completed.stdout)
        streams = payload.get("streams", [])
        video_stream = next((s for s in streams if s.get("width") and s.get("height")), {})
        duration = payload.get("format", {}).get("duration")
        result.update({
            "duration_seconds": round(float(duration), 2) if duration else None,
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "metadata_available": True,
        })
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        pass
    return result
