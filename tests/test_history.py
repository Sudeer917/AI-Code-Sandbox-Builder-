import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_history_and_stats_flow():
    # 1. Run a code execution
    client.post("/api/run", json={"filename": "test.py", "language": "python", "code": 'print("Test Run")'})

    # 2. Check history listing
    hist_resp = client.get("/api/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) > 0

    latest_id = history[0]["id"]

    # 3. Fetch single history session
    item_resp = client.get(f"/api/history/{latest_id}")
    assert item_resp.status_code == 200
    assert item_resp.json()["id"] == latest_id

    # 4. Fetch dashboard stats
    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_executions"] > 0

    # 5. Delete item
    del_resp = client.delete(f"/api/history/{latest_id}")
    assert del_resp.status_code == 200
