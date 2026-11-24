from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import StoryboardRequest
from app.services.storyboard import normalize_ai_storyboard

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_storyboard_has_five_scenes_when_template_enabled(monkeypatch):
    monkeypatch.setattr("app.main.DEMO_MODE", True)
    response = client.post("/api/storyboard", json={
        "destination": "Coorg",
        "trip_description": "Coffee estates, waterfalls and a road trip",
        "mood": "warm cinematic",
        "target_duration_seconds": 60,
        "aspect_ratio": "9:16",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["destination"] == "Coorg"
    assert len(payload["scenes"]) == 5
    assert payload["target_duration_seconds"] == 60
    assert payload["generation_mode"] == "template"


def test_storyboard_rejects_invalid_aspect_ratio():
    response = client.post("/api/storyboard", json={"aspect_ratio": "4:3"})
    assert response.status_code == 422


def test_media_list_returns_assets_array():
    response = client.get("/api/media")
    assert response.status_code == 200
    assert isinstance(response.json()["assets"], list)


def test_ai_status_reports_local_provider(monkeypatch):
    monkeypatch.setattr("app.main.DEMO_MODE", False)
    monkeypatch.setattr("app.main.OLLAMA_ENABLED", True)
    with patch("app.main.get_ollama_status", return_value={
        "provider": "ollama", "enabled": True, "available": True,
        "model": "qwen2.5:3b", "message": "Connected",
    }):
        response = client.get("/api/ai/status")
    assert response.status_code == 200
    assert response.json()["provider"] == "ollama"
    assert response.json()["available"] is True


def test_storyboard_uses_ollama_when_enabled(monkeypatch):
    monkeypatch.setattr("app.main.DEMO_MODE", False)
    monkeypatch.setattr("app.main.OLLAMA_ENABLED", True)
    expected = {"generation_mode": "ollama", "scenes": []}
    with patch("app.main.generate_storyboard", return_value=expected) as generate:
        response = client.post("/api/storyboard", json={"destination": "Coorg"})
    assert response.status_code == 200
    assert response.json() == expected
    generate.assert_called_once()


def test_storyboard_uses_template_in_demo_mode(monkeypatch):
    monkeypatch.setattr("app.main.DEMO_MODE", True)
    monkeypatch.setattr("app.main.OLLAMA_ENABLED", True)
    response = client.post("/api/storyboard", json={"destination": "Coorg"})
    assert response.status_code == 200
    assert response.json()["generation_mode"] == "template"


def test_ai_storyboard_normalizes_scene_timing():
    request = StoryboardRequest(destination="Coorg", target_duration_seconds=45)
    generated = {
        "title": "Misty Coorg",
        "trip_summary": "A misty escape",
        "scenes": [
            {"title": f"Scene {i}", "direction": "Show the moment", "suggested_shot": "wide", "duration_seconds": i}
            for i in range(1, 6)
        ],
    }
    board = normalize_ai_storyboard(request, generated)
    assert len(board["scenes"]) == 5
    assert board["scenes"][0]["start_seconds"] == 0
    assert sum(scene["duration_seconds"] for scene in board["scenes"]) == 45
    assert board["generation_mode"] == "ollama"


def test_ai_storyboard_rejects_invalid_scene_count():
    request = StoryboardRequest()
    try:
        normalize_ai_storyboard(request, {"scenes": []})
    except ValueError as exc:
        assert "exactly five" in str(exc)
    else:
        raise AssertionError("Expected invalid AI scene count to fail")
