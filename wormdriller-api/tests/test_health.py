from fastapi.testclient import TestClient
from app.enhanced_main import app

client = TestClient(app)

def test_health():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
