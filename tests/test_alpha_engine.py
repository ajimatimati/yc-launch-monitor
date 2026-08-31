"""
Unit and Integration Tests for Unified Alpha Engine:
- MintDash Telegram Notifier
- Non-custodial PBKDF2 Wallet Vault
- On-chain Smart Money Mint Scanner
- GitHub Cash Bounty Hunter
- Pond Protocol V1 Alpha Actions
"""

import pytest
from fastapi.testclient import TestClient
from yc_launch_monitor.pond.server import app
from yc_launch_monitor.telegram.notifier import telegram_notifier
from yc_launch_monitor.web3_vault.wallet_vault import wallet_vault, WalletVault
from yc_launch_monitor.web3_vault.simulator import tx_simulator
from yc_launch_monitor.monitors.onchain_mints import onchain_mint_monitor
from yc_launch_monitor.monitors.bounty_scout import bounty_scout_monitor
from yc_launch_monitor.config import settings

client = TestClient(app)

def test_telegram_notifier_configured():
    assert telegram_notifier.is_configured is True
    assert telegram_notifier.bot_token.startswith("7740806969:")
    assert telegram_notifier.chat_id == "7899086191"

def test_wallet_vault_creation_and_encryption(tmp_path):
    vault_file = str(tmp_path / "test_vault.json")
    vault = WalletVault(vault_path=vault_file, password="test_master_password_123")
    
    # Create wallet
    w1 = vault.create_wallet(label="GTM Alpha Vault #1")
    assert w1.address.startswith("0x")
    assert len(w1.address) == 42
    assert len(vault.wallets) == 1
    
    # Re-open vault with correct password
    vault2 = WalletVault(vault_path=vault_file, password="test_master_password_123")
    assert len(vault2.wallets) == 1
    assert w1.address.lower() in vault2.wallets

def test_onchain_mint_monitor():
    mints = onchain_mint_monitor.scan_mints(send_telegram=False)
    assert len(mints) > 0
    first = mints[0]
    assert first.contract_name != ""
    assert first.chain in ["base", "ethereum", "arbitrum"]
    assert first.contract_address.startswith("0x")

def test_bounty_scout_monitor():
    bounties = bounty_scout_monitor.scan_bounties(send_telegram=False)
    assert len(bounties) > 0
    first = bounties[0]
    assert first.reward_usd >= 50.0
    assert first.repo != ""
    assert first.issue_url.startswith("https://github.com/")

def test_api_bounties_and_onchain_endpoints():
    r1 = client.get("/api/bounties")
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    r2 = client.get("/api/onchain-mints")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    r3 = client.get("/api/wallet/status")
    assert r3.status_code == 200
    data3 = r3.json()
    assert "wallet_count" in data3
    assert data3["simulation_only"] is True

def test_pond_run_hunt_bounties_action():
    payload = {
        "action_id": "hunt_bounties",
        "parameters": {"min_reward_usd": 100.0}
    }
    headers = {
        "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
        "Content-Type": "application/json"
    }
    res = client.post("/runs", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "GitHub Cash Bounties" in data["output"][0]["text"]

def test_pond_run_scan_onchain_alpha_action():
    payload = {
        "action_id": "scan_onchain_alpha",
        "parameters": {"chain": "base"}
    }
    headers = {
        "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
        "Content-Type": "application/json"
    }
    res = client.post("/runs", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "On-Chain Smart Money Mints" in data["output"][0]["text"]

def test_pond_run_get_wallet_status_action():
    payload = {
        "action_id": "get_wallet_status",
        "parameters": {}
    }
    headers = {
        "Authorization": f"Bearer {settings.POND_ACCESS_KEY}",
        "Content-Type": "application/json"
    }
    res = client.post("/runs", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "Web3 Non-Custodial Wallet Vault Status" in data["output"][0]["text"]
