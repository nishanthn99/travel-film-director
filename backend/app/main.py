from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .schemas import RenderRequest, StoryboardRequest
from .services.media import inspect_media, is_video
from .services.storyboard import build_storyboard
from .services.renderer import render_video

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("TFD_DATA_DIR", BASE_DIR / "data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = int(os.getenv("TFD_MAX_UPLOAD_BYTES", str(500 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".jpg", ".jpeg", ".png", ".webp"}

app = FastAPI(title="Travel Film Director API", version="0.1.0")
allowed_origins = [origin.strip() for origin in os.getenv("TFD_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "travel-film-director-api"}


@app.get("/api/media")
def list_media() -> dict[str, list[dict]]:
    assets = []
    for path in sorted(UPLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            metadata = inspect_media(path)
            assets.append({"id": path.stem, "name": path.name, **metadata})
    return {"assets": assets}


@app.post("/api/media/upload")
async def upload_media(files: Annotated[list[UploadFile], File(...)]) -> dict[str, list[dict]]:
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one media file.")

    saved = []
    for upload in files:
        original_name = Path(upload.filename or "upload").name
        suffix = Path(original_name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {suffix or 'unknown'}")

        asset_id = uuid.uuid4().hex
        destination = UPLOAD_DIR / f"{asset_id}{suffix}"
        total = 0
        try:
            with destination.open("wb") as output:
                while chunk := await upload.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail=f"{original_name} exceeds the 500 MB upload limit.")
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

        if total == 0:
            destination.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"{original_name} is empty.")

        saved.append({
            "id": asset_id,
            "name": original_name,
            "size_bytes": total,
            **inspect_media(destination),
        })
    return {"assets": saved}


@app.post("/api/storyboard")
def create_storyboard(request: StoryboardRequest) -> dict:
    return build_storyboard(request)


@app.post("/api/render")
def create_render(request: RenderRequest) -> dict:
    selected = []
    for asset_id in request.asset_ids:
        matches = list(UPLOAD_DIR.glob(f"{asset_id}.*"))
        if not matches:
            raise HTTPException(status_code=404, detail=f"Media asset not found: {asset_id}")
        path = matches[0].resolve()
        if path.parent != UPLOAD_DIR or not is_video(path):
            continue
        selected.append(path)

    if not selected:
        raise HTTPException(status_code=400, detail="Select at least one video clip to render.")

    try:
        result = render_video(
            selected,
            EXPORT_DIR,
            request.aspect_ratio,
            request.title,
            request.clip_seconds,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result


app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")
