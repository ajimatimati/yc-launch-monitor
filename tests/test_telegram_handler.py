"""
Unit tests for Telegram Webhook & Mobile Command Controller.
"""

import pytest
from fastapi.testclient import TestClient
from yc_launch_monitor.pond.server import app
from yc_launch_monitor.telegram.handler import telegram_handler
from yc_launch_monitor.config import settings

client = TestClient(app)

def test_telegram_webhook_start_command():
    payload = {
        "update_id": 1001,
        "message": {
            "message_id": 1,
            "chat": {"id": 7899086191},
            "text": "/start"
        }
    }
    res = client.post("/api/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

def test_telegram_webhook_stats_command():
    payload = {
        "update_id": 1002,
        "message": {
            "message_id": 2,
            "chat": {"id": 7899086191},
            "text": "/stats"
        }
    }
    res = client.post("/api/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

def test_telegram_webhook_early_command():
    payload = {
        "update_id": 1003,
        "message": {
            "message_id": 3,
            "chat": {"id": 7899086191},
            "text": "/early"
        }
    }
    res = client.post("/api/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

def test_telegram_webhook_mints_command():
    payload = {
        "update_id": 1004,
        "message": {
            "message_id": 4,
            "chat": {"id": 7899086191},
            "text": "/mints"
        }
    }
    res = client.post("/api/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

def test_telegram_webhook_bounties_command():
    payload = {
        "update_id": 1005,
        "message": {
            "message_id": 5,
            "chat": {"id": 7899086191},
            "text": "/bounties"
        }
    }
    res = client.post("/api/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

def test_telegram_webhook_callback_query_button():
    payload = {
        "update_id": 1006,
        "callback_query": {
            "id": "cb_1",
            "message": {
                "message_id": 10,
                "chat": {"id": 7899086191}
            },
            "data": "cmd_vault"
        }
    }
    res = client.post("/api/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}
