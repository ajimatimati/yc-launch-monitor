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

    # Monitoring Settings
    POLL_INTERVAL_HOURS: int = 8
    TARGET_BATCHES: str = "S26,W26,F26,S25,SR006,SR007,SR005"
    
    ENABLE_YC_DIRECTORY: bool = True
    ENABLE_SPEEDRUN_DIRECTORY: bool = True
    ENABLE_X_TWITTER: bool = True
    ENABLE_LINKEDIN: bool = True

    # Social Media API Keys (Optional with built-in fallbacks)
    TWITTER_BEARER_TOKEN: Optional[str] = None
    LINKEDIN_API_KEY: Optional[str] = None

    # Database
    DATABASE_PATH: str = str(BASE_DIR / "yc_launches.db")

    # Pond Agent Protocol
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    POND_ACCESS_KEY: str = "pond_sk_yc_launch_monitor_2026"

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
