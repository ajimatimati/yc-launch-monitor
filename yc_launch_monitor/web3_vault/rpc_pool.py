"""
Multi-Chain Failover RPC Pool for Base, Ethereum, and Arbitrum.
"""

from __future__ import annotations
import logging
import urllib.request
import json
from typing import Dict, List, Optional, Any

from ..config import settings

logger = logging.getLogger(__name__)

CHAIN_IDS = {
    "base": 8453,
    "ethereum": 1,
    "arbitrum": 42161
}

class RPCPool:
    """Manages RPC endpoints with automatic failover and JSON-RPC calls."""

    def __init__(self):
        self.rpc_map: Dict[str, List[str]] = {
            "base": [u.strip() for u in settings.BASE_RPC_URLS.split(",") if u.strip()],
            "ethereum": [u.strip() for u in settings.ETHEREUM_RPC_URLS.split(",") if u.strip()],
            "arbitrum": [u.strip() for u in settings.ARBITRUM_RPC_URLS.split(",") if u.strip()]
        }

    def call_rpc(self, chain: str, method: str, params: List[Any]) -> Optional[Any]:
        """Executes a JSON-RPC request with failover support."""
        urls = self.rpc_map.get(chain.lower(), self.rpc_map["base"])
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }).encode("utf-8")

        for url in urls:
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "MintDash/1.0"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if "result" in data:
                        return data["result"]
            except Exception as e:
                logger.warning(f"[RPCPool] RPC {url} failed: {e}. Trying next...")
                continue
        return None

    def get_block_number(self, chain: str = "base") -> int:
        res = self.call_rpc(chain, "eth_blockNumber", [])
        if res:
            return int(res, 16)
        return 0

rpc_pool = RPCPool()
