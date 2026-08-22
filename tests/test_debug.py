import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_critical_end_to_end_debug_flow():
    """
    Critical Test specified in prompt section 36:
    Input code:
    def calculate_average(numbers):
        total = sum(numbers)
        average = total / len(number)
        return average

    numbers = [10, 20, 30, 40]
    print("Average:", calculate_average(numbers))

    Expected Result:
    - NameError detected for len(number)
    - Fix generated: number -> numbers
    - Code re-executed and verified
    - Output: Average: 25.0
    - Exit code: 0
    """
    code_with_bug = """def calculate_average(numbers):
    total = sum(numbers)
    average = total / len(number)
    return average

numbers = [10, 20, 30, 40]

print("Average:", calculate_average(numbers))"""

    payload = {
        "filename": "script.py",
        "language": "python",
        "code": code_with_bug
    }

    response = client.post("/api/debug", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["error_type"] == "NameError"
    assert "numbers" in data["fixed_code"]
    assert "Average: 25.0" in data["stdout"]
    assert data["exit_code"] == 0
