from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_storyboard_has_five_scenes():
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


def test_storyboard_rejects_invalid_aspect_ratio():
    response = client.post("/api/storyboard", json={"aspect_ratio": "4:3"})
    assert response.status_code == 422


def test_media_list_returns_assets_array():
    response = client.get("/api/media")
    assert response.status_code == 200
    assert isinstance(response.json()["assets"], list)
