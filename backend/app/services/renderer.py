from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path


SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}


def render_video(clips: list[Path], export_dir: Path, aspect_ratio: str, title: str, clip_seconds: int) -> dict:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed or not available on PATH. Install FFmpeg to render videos.")

    width, height = SIZES[aspect_ratio]
    output_name = f"travel-film-{uuid.uuid4().hex[:10]}.mp4"
    output_path = export_dir / output_name
    args = [ffmpeg, "-y"]
    for clip in clips:
        args.extend(["-i", str(clip)])

    filters = []
    labels = []
    for index in range(len(clips)):
        label = f"v{index}"
        filters.append(
            f"[{index}:v]trim=duration={clip_seconds},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,fps=30,format=yuv420p[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append("".join(labels) + f"concat=n={len(clips)}:v=1:a=0[outv]")

    args.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[outv]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "23", "-movflags", "+faststart", str(output_path),
    ])
    try:
        subprocess.run(args, capture_output=True, text=True, timeout=900, check=True)
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError("Rendering timed out after 15 minutes. Try fewer or shorter clips.") from exc
    except subprocess.CalledProcessError as exc:
        output_path.unlink(missing_ok=True)
        detail = (exc.stderr or "Unknown FFmpeg error")[-1200:]
        raise RuntimeError(f"FFmpeg could not render this selection: {detail}") from exc

    return {
        "status": "completed",
        "filename": output_name,
        "url": f"/exports/{output_name}",
        "clip_count": len(clips),
        "aspect_ratio": aspect_ratio,
        "title": title,
    }
