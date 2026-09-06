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
    assert "Executive GTM Dashboard" in resp.text
    assert "Ajimati" in resp.text

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

def test_pond_task_endpoint_unauthorized():
    # Unauthenticated request must return 401
    resp = client.get("/tasks/task_12345")
    assert resp.status_code == 401
    assert resp.json().get("code") == "unauthorized"

def test_pond_task_endpoint_authorized():
    # Authenticated request must return 200 with result
    headers = {"Authorization": f"Bearer {settings.POND_ACCESS_KEY}"}
    resp = client.get("/tasks/task_12345", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "completed"
    assert data.get("task_id") == "task_12345"

def test_pond_task_list_endpoint():
    # Unauthorized returns 401
    assert client.get("/tasks").status_code == 401
    # Authorized returns 200 with task definitions
    headers = {"Authorization": f"Bearer {settings.POND_ACCESS_KEY}"}
    resp = client.get("/tasks", headers=headers)
    assert resp.status_code == 200
    assert "tasks" in resp.json()

def test_monitoring_freshness_never_stale():
    from yc_launch_monitor.database import db
    import datetime
    stats = db.get_stats()
    assert stats.last_scan_time is not None
    last_dt = datetime.datetime.fromisoformat(stats.last_scan_time)
    now = datetime.datetime.now(datetime.timezone.utc)
    # Must be fresh (less than 2 hours old, never 107 hours stale)
    assert (now - last_dt).total_seconds() < 7200

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

def test_pond_run_agent_standard():
    body = {
        "run_id": "run_agent_test_01",
        "action_id": "run_agent",
        "parameters": {"prompt": "Show early signals from YC S26"}
    }
    headers = {
        "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
        "X-Agent-Protocol-Version": "1.0"
    }
    resp = client.post("/runs", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "usage" in data

def test_pond_run_agent_fail_directive():
    body = {
        "run_id": "run_agent_fail_01",
        "action_id": "run_agent",
        "parameters": {"prompt": "fail"}
    }
    headers = {
        "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
        "X-Agent-Protocol-Version": "1.0"
    }
    resp = client.post("/runs", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "failed"
    assert "error" in data
    assert data["usage"]["quantity"] == 0

