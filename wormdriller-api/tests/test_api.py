from fastapi.testclient import TestClient
from app.enhanced_main import app

client = TestClient(app)

def test_wellpath_endpoint():
    payload = {
        "well_id": "test",
        "survey_name": "survey1",
        "calculation_method": "minimum_curvature",
        "survey_points": [
            {"md": 0.0, "inc": 0.0, "azi": 0.0},
            {"md": 1000.0, "inc": 1.0, "azi": 45.0}
        ]
    }
    resp = client.post("/api/v1/calculations/wellpath", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "wellpath" in data
