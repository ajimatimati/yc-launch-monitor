import pytest
from fastapi.testclient import TestClient
from yc_launch_monitor.pond.server import app
from yc_launch_monitor.config import settings

client = TestClient(app)

def test_dashboard_ui_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "YC Launch Monitor" in resp.text
    assert "Rho GTM Radar" in resp.text

def test_api_stats_and_launches():
    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    assert "total_tracked_companies" in stats_resp.json()

    launches_resp = client.get("/api/launches?limit=10")
    assert launches_resp.status_code == 200
    assert isinstance(launches_resp.json(), list)

def test_pond_manifest_public():
    resp = client.get("/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("protocol") == "marketplace-agent"
    assert data.get("protocol_version") == "1.0"
    assert "actions" in data
    assert "capabilities" in data
    assert "metadata" in data

def test_pond_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"
    assert "components" in data
    assert data["components"]["database"]["status"] == "up"

def test_pond_run_unauthorized():
    body = {
        "run_id": "run_test_unauth",
        "action_id": "get_monitor_status",
        "parameters": {}
    }
    # No auth header
    resp = client.post("/runs", json=body, headers={"X-Agent-Protocol-Version": "1.0"})
    assert resp.status_code == 401

    # Wrong auth key
    resp2 = client.post(
        "/runs",
        json=body,
        headers={
            "Authorization": "Bearer wrong_key",
            "X-Agent-Protocol-Version": "1.0"
        }
    )
    assert resp2.status_code == 401

def test_pond_run_invalid_protocol_version():
    body = {
        "run_id": "run_test_ver",
        "action_id": "get_monitor_status",
        "parameters": {}
    }
    resp = client.post(
        "/runs",
        json=body,
        headers={
            "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
            "X-Agent-Protocol-Version": "2.0"
        }
    )
    assert resp.status_code == 400

def test_pond_run_get_monitor_status():
    body = {
        "run_id": "run_test_valid_01",
        "agent_id": "agt_yc_radar",
        "conversation_id": "conv_123",
        "history_truncated": False,
        "action_id": "get_monitor_status",
        "user": {"id": "usr_1", "locale": "en-US", "timezone": "America/Los_Angeles"},
        "messages": [{"id": "m1", "role": "user", "created_at": "2026-08-29T12:00:00Z", "parts": [{"type": "text", "text": "Status"}]}],
        "parameters": {},
        "execution": {"accepted_output_modes": ["text/markdown"], "deadline_ms": 30000}
    }
    resp = client.post(
        "/runs",
        json=body,
        headers={
            "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
            "X-Agent-Protocol-Version": "1.0",
            "Idempotency-Key": "run_test_valid_01"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("run_id") == "run_test_valid_01"
    assert data.get("status") == "completed"
    assert len(data.get("output", [])) > 0
    assert "usage" in data
    assert data["usage"]["unit_of_measurement"] == "result"

def test_pond_run_idempotency():
    body = {
        "run_id": "run_idempotent_test",
        "action_id": "get_monitor_status",
        "parameters": {}
    }
    headers = {
        "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
        "X-Agent-Protocol-Version": "1.0",
        "Idempotency-Key": "run_idempotent_test"
    }
    resp1 = client.post("/runs", json=body, headers=headers)
    resp2 = client.post("/runs", json=body, headers=headers)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()
