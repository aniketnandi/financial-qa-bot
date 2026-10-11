from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_health_check():
    assert client.get("/").json()["status"] == "ok"


def test_empty_question_is_rejected():
    for path in ("/ask", "/ask_agent"):
        assert client.post(path, json={"question": "   "}).status_code == 400


def test_missing_index_returns_503(monkeypatch):
    monkeypatch.setattr(main, "INDEX_DIR", "does_not_exist")
    resp = client.post("/ask", json={"question": "What was revenue?"})
    assert resp.status_code == 503
    assert "ingest.py" in resp.json()["detail"]
