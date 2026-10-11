from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.backend.main import app


def test_tutor_websocket_returns_a_reply() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws/tutor") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "ready"

            websocket.send_json(
                {
                    "type": "message",
                    "problemId": 1,
                    "language": "python",
                    "code": "def solve(nums):\n    return nums",
                    "question": "How should I think about this problem?",
                    "mode": "explain",
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "message"
            assert response["role"] == "assistant"
            assert response["content"]


def test_tutor_websocket_falls_back_when_openai_errors(monkeypatch) -> None:
    def raise_runtime_error(*args, **kwargs):
        raise RuntimeError("OpenAI service unavailable")

    monkeypatch.setattr("apps.backend.ai_services.call_openai_tutor", raise_runtime_error)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/tutor") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "ready"

            websocket.send_json(
                {
                    "type": "message",
                    "problemId": 1,
                    "language": "python",
                    "code": "def solve(nums):\n    return nums",
                    "question": "How should I think about this problem?",
                    "mode": "explain",
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "message"
            assert response["role"] == "assistant"
            assert response["content"]
            assert "I can help you work through this explain style" in response["content"]
