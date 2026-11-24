import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["keys_configured"] >= 2
    assert data["cache_enabled"] is True


def test_unknown_session_returns_404():
    response = client.get(
        "/sessions/session-that-does-not-exist/messages"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "session not found"
    }


def test_empty_message_returns_422():
    response = client.post(
        "/chat",
        json={
            "session_id": "validation-test",
            "message": "     ",
            "system_prompt": None
        }
    )

    assert response.status_code == 422
def test_all_keys_simulated_failure_returns_503():
    response = client.post(
        "/chat",
        headers={
            "X-Simulate-Failure": "*=429"
        },
        json={
            "session_id": "simulated-all-fail-test",
            "message": "This request should fail",
            "system_prompt": None
        }
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "all providers unavailable"
    }