import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_infinite_loop_timeout():
    """
    Test 5 from Section 35:
    while True:
        pass
    Expected: TimeoutError, process terminated within configured limit.
    """
    payload = {
        "filename": "infinite.py",
        "language": "python",
        "code": "while True:\n    pass"
    }

    # Override timeout to 2 seconds for quick test
    from backend.config import settings
    original_timeout = settings.SANDBOX_TIMEOUT
    settings.SANDBOX_TIMEOUT = 2

    try:
        response = client.post("/api/run", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["timed_out"] is True
        assert data["error_type"] == "TimeoutError"
        assert "Timed Out" in data["stderr"]
    finally:
        settings.SANDBOX_TIMEOUT = original_timeout
