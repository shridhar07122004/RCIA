import io

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_sample_text_and_run_analysis():
    client.post("/api/health")
    document = client.post("/api/documents/upload", files={"file": ("sample.md", io.BytesIO(b"FR-01: Users can log in using email and password.\nFR-02: The system validates the password before a session."), "text/markdown")})
    assert document.status_code == 200, document.text
    payload = document.json()
    assert payload["document"]["requirement_count"] == 2
    analysis = client.post("/api/analysis", json={"document_id": payload["document"]["id"], "change_type": "add", "proposed_change": "Add OTP verification after password validation during login."})
    assert analysis.status_code == 200, analysis.text
    assert "result" in analysis.json()
