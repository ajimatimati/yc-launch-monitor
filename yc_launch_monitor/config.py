import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Slack Configuration
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_ID: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Telegram MintDash Configuration
    TELEGRAM_BOT_TOKEN: str = "7740806969:AAG_zC8L6a3-b8t4BroNtnvMXN_MVW1BCl0"
    TELEGRAM_CHAT_ID: str = "7899086191"

    # Web3 & On-Chain Mint Settings (Zero-Risk Simulation Mode by default)
    DEFAULT_CHAIN: str = "base"
    MAX_TASK_SPEND_ETH: float = 0.01
    MAX_FEE_GWEI: float = 30.0
    PRIORITY_FEE_GWEI: float = 1.0
    VAULT_FILE: str = str(BASE_DIR / "data" / "vault.json")
    SIMULATION_ONLY: bool = True

    # Multi-Chain RPCs
    BASE_RPC_URLS: str = "https://mainnet.base.org,https://base.llamarpc.com"
    ETHEREUM_RPC_URLS: str = "https://cloudflare-eth.com,https://eth.llamarpc.com"
    ARBITRUM_RPC_URLS: str = "https://arb1.arbitrum.io/rpc"

    # GitHub Bounty Scout
    ENABLE_BOUNTY_SCOUT: bool = True
    MIN_BOUNTY_USD: float = 50.0

    # Monitoring Settings
    POLL_INTERVAL_HOURS: int = 8
    TARGET_BATCHES: str = "S26,W26,F26,S25,SR006,SR007,SR005"
    
    ENABLE_YC_DIRECTORY: bool = True
    ENABLE_SPEEDRUN_DIRECTORY: bool = True
    ENABLE_X_TWITTER: bool = True
    ENABLE_LINKEDIN: bool = True
    ENABLE_ONCHAIN_MINTS: bool = True

    # Social Media API Keys (Optional with built-in fallbacks)
    TWITTER_BEARER_TOKEN: Optional[str] = None
    LINKEDIN_API_KEY: Optional[str] = None

    # Database
    DATABASE_PATH: str = str(BASE_DIR / "yc_launches.db")

    # Pond Agent Protocol
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    POND_ACCESS_KEY: str = "kYmQRiFJfVDdzl0ESFa4TvghaNpSBUDR"

    # GTM Profile
    GTM_CONTACT_NAME: str = "Jayson Fung"
    GTM_CONTACT_EMAIL: str = "jayson@rho.co"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def target_batch_list(self) -> List[str]:
        """Returns normalized uppercase list of target batch strings."""
        return [b.strip().upper() for b in self.TARGET_BATCHES.split(",") if b.strip()]

# Global settings instance
settings = Settings()
