from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_particle_endpoint() -> None:
    response = client.get("/api/v1/particles/pi+")
    assert response.status_code == 200
    assert response.json()["pdgid"] == 211


def test_generate_phase_space_from_particle_names() -> None:
    response = client.post(
        "/api/v1/phase-space/generate",
        json={
            "mother": {"name": "D0"},
            "daughters": [
                {"name": "pi+"},
                {"name": "pi-"},
                {"name": "pi0"},
            ],
            "n_events": 10,
            "seed": 7,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["unit"] == "GeV"
    assert len(body["events"]) == 10
    assert body["mother"]["pdgid"] == 421
