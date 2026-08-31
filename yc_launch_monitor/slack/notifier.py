from __future__ import annotations
import json
import logging
import requests
from typing import Optional, Dict, Any, Tuple, List

from .block_kit import SlackBlockBuilder
from ..models import LaunchItem
from ..config import settings

logger = logging.getLogger(__name__)

class SlackNotifier:
    """
    Sends alerts to Slack using Bot User OAuth token, Webhook, or local Rich terminal preview.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        channel_id: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        self._bot_token = bot_token
        self._channel_id = channel_id
        self._webhook_url = webhook_url

    @property
    def bot_token(self) -> Optional[str]:
        from ..database import db
        return self._bot_token or settings.SLACK_BOT_TOKEN or db.get_config("slack_bot_token")

    @property
    def channel_id(self) -> Optional[str]:
        from ..database import db
        return self._channel_id or settings.SLACK_CHANNEL_ID or db.get_config("slack_channel_id")

    @property
    def webhook_url(self) -> Optional[str]:
        from ..database import db
        return self._webhook_url or settings.SLACK_WEBHOOK_URL or db.get_config("slack_webhook_url")

    @property
    def is_configured(self) -> bool:
        return bool((self.bot_token and self.channel_id) or self.webhook_url)

    def send_launch_alert(self, item: LaunchItem, dry_run: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Dispatches Slack alert for a launch item.
        Returns:
            (success, message_timestamp_or_id)
        """
        payload = SlackBlockBuilder.build_alert_payload(item)

        if dry_run or not self.is_configured:
            self._render_local_preview(item, payload)
            return True, f"mock_ts_{item.id}"

        # Method 1: Slack Web API (chat.postMessage)
        if self.bot_token and self.channel_id:
            try:
                url = "https://slack.com/api/chat.postMessage"
                headers = {
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json; charset=utf-8"
                }
                body = {
                    "channel": self.channel_id,
                    "text": payload["text"],
                    "blocks": payload["blocks"],
                    "unfurl_links": False,
                    "unfurl_media": False
                }
                resp = requests.post(url, headers=headers, json=body, timeout=10)
                resp_json = resp.json()
                
                if resp_json.get("ok"):
                    ts = resp_json.get("ts")
                    logger.info(f"Slack alert sent successfully for {item.company_name} (ts: {ts})")
                    return True, ts
                else:
                    logger.error(f"Slack API error: {resp_json.get('error')}")
            except Exception as e:
                logger.error(f"Failed to post Slack message via Web API: {e}")

        # Method 2: Incoming Webhook fallback
        if self.webhook_url:
            try:
                resp = requests.post(self.webhook_url, json=payload, timeout=10)
                if resp.status_code == 200:
                    logger.info(f"Slack alert sent via webhook for {item.company_name}")
                    return True, "webhook_delivered"
                else:
                    logger.error(f"Slack Webhook returned HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Failed to post Slack message via Webhook: {e}")

        return False, None

    def _render_local_preview(self, item: LaunchItem, payload: Dict[str, Any]):
        """Renders rich terminal representation when running in local preview or dry run."""
        try:
            import sys
            if hasattr(sys.stdout, "reconfigure"):
                try:
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
            from rich.console import Console
            from rich.panel import Panel
            from rich.text import Text
            
            console = Console(force_terminal=True, legacy_windows=False)
            is_early = "EARLY" in payload["text"]
            border_color = "yellow" if is_early else "green"

            content = Text()
            content.append(f"📡 SLACK BOT ALERT DISPATCH (Preview)\n", style="bold underline")
            content.append(f"{payload['text']}\n\n", style="bold yellow" if is_early else "bold green")
            content.append(f"Company:  ", style="bold")
            content.append(f"{item.company_name} ({item.website or 'No URL'})\n")
            content.append(f"Founder:  ", style="bold")
            content.append(f"{item.display_founder}\n")
            content.append(f"Batch:    ", style="bold")
            content.append(f"{item.batch or 'YC Current'}\n")
            content.append(f"Source:   ", style="bold")
            content.append(f"{item.source.value}\n")
            content.append(f"Status:   ", style="bold")
            content.append(f"{item.status.value}\n")
            
            if item.post_text:
                content.append(f"\nOriginal Post:\n", style="bold cyan")
                content.append(f"\"{item.post_text}\"\n", style="italic")
            
            if item.post_url:
                content.append(f"\nPost Link: {item.post_url}\n", style="dim")

            console.print(Panel(content, title=f"Slack Alert: {item.company_name}", border_style=border_color))
        except Exception:
            print(f"[Slack Preview] {payload['text']} - {item.company_name} ({item.primary_link})")

from typing import Tuple

# Global notifier instance
slack_notifier = SlackNotifier()
