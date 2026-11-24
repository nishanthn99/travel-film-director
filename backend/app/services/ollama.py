from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot generate a storyboard."""


def _base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def configured_model() -> str:
    return os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()


def _timeout() -> float:
    try:
        return max(1.0, float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180")))
    except ValueError:
        return 180.0


def _request_json(path: str, payload: dict | None = None, timeout: float = 8.0) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{_base_url()}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise OllamaError(
            f"Cannot reach Ollama at {_base_url()}. Start Ollama and make sure its local API is available. Details: {exc}"
        ) from exc


def get_ollama_status() -> dict:
    model = configured_model()
    try:
        payload = _request_json("/api/tags", timeout=4.0)
        installed = {
            item.get("name") or item.get("model")
            for item in payload.get("models", [])
            if isinstance(item, dict)
        }
        if model not in installed:
            return {
                "provider": "ollama",
                "enabled": True,
                "available": False,
                "model": model,
                "message": f"Ollama is running, but {model} is not installed. Run: ollama pull {model}",
            }
        return {
            "provider": "ollama",
            "enabled": True,
            "available": True,
            "model": model,
            "message": f"Connected to local Ollama ({model}).",
        }
    except OllamaError as exc:
        return {
            "provider": "ollama",
            "enabled": True,
            "available": False,
            "model": model,
            "message": str(exc),
        }


def generate_storyboard(request) -> dict:
    from ..services.storyboard import normalize_ai_storyboard

    model = configured_model()
    prompt = f"""
You are an experienced travel-film editor and story producer.
Create a practical, emotionally coherent storyboard for a travel film.
Return one JSON object only, with this exact shape:
{{
  "title": "short film title",
  "trip_summary": "one sentence summary",
  "scenes": [
    {{
      "title": "scene title",
      "direction": "specific editing and storytelling direction",
      "suggested_shot": "short shot type",
      "duration_seconds": 8
    }}
  ]
}}
Create exactly five scenes. Their duration suggestions must be positive numbers.
Make the scene choices specific to the trip, destination and mood. Avoid claiming to have
analysed footage; no footage or frames have been supplied to this storyboard model.
The requested final film duration is {request.target_duration_seconds} seconds.
Destination: {request.destination}
Trip details: {request.trip_description or "Not provided"}
Mood: {request.mood}
Aspect ratio: {request.aspect_ratio}
""".strip()
    payload = _request_json(
        "/api/chat",
        {
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": "You create useful travel-film storyboards. Follow the requested JSON schema exactly.",
                },
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.7},
        },
        timeout=_timeout(),
    )
    try:
        content = payload["message"]["content"]
        generated = json.loads(content)
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise OllamaError("Ollama returned an invalid storyboard response. Try another model or retry.") from exc
    return normalize_ai_storyboard(request, generated)
