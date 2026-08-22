import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI Code Sandbox"

def test_run_hello_world():
    payload = {
        "filename": "script.py",
        "language": "python",
        "code": 'print("Hello World")'
    }
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Hello World" in data["stdout"]
    assert data["exit_code"] == 0

def test_run_zero_division_error():
    payload = {
        "filename": "script.py",
        "language": "python",
        "code": "x = 10\ny = 0\nprint(x / y)"
    }
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "ZeroDivisionError" in data["stderr"]
    assert data["exit_code"] != 0
