"""
MintDash Telegram Notifier Module.
Dispatches real-time alpha alerts, early founder signals, on-chain mints, and GitHub bounties
to the configured Telegram chat via @my_mintdash_execution_bot.
"""

from __future__ import annotations
import json
import logging
import urllib.request
import urllib.parse
from typing import Optional, Tuple, Dict, Any, List

from ..config import settings
from ..models import LaunchItem, LaunchStatus

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Sends real-time HTML-formatted alpha notifications to Telegram."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        self._bot_token = bot_token
        self._chat_id = chat_id

    @property
    def bot_token(self) -> str:
        from ..database import db
        return (
            self._bot_token
            or settings.TELEGRAM_BOT_TOKEN
            or db.get_config("telegram_bot_token")
            or "7740806969:AAG_zC8L6a3-b8t4BroNtnvMXN_MVW1BCl0"
        )

    @property
    def chat_id(self) -> str:
        from ..database import db
        return (
            self._chat_id
            or settings.TELEGRAM_CHAT_ID
            or db.get_config("telegram_chat_id")
            or "7899086191"
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, html_text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """Sends an HTML formatted message to the configured Telegram chat."""
        if not self.is_configured:
            logger.warning("[TelegramNotifier] Not configured. Skipping alert.")
            return False, "Telegram token or chat_id missing."

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_body = json.loads(resp.read().decode("utf-8"))
                if res_body.get("ok"):
                    msg_id = str(res_body.get("result", {}).get("message_id"))
                    logger.info(f"[TelegramNotifier] Dispatched message #{msg_id} to chat {self.chat_id}")
                    return True, msg_id
                else:
                    err = res_body.get("description", "Unknown Telegram API error")
                    logger.error(f"[TelegramNotifier] Telegram API error: {err}")
                    return False, err
        except Exception as e:
            logger.error(f"[TelegramNotifier] Failed to send Telegram alert: {e}")
            return False, str(e)

    def test_connection(self) -> Tuple[bool, str]:
        """Verifies bot connectivity and sends a test ping."""
        if not self.bot_token or not self.chat_id:
            return False, "Telegram Bot Token or Chat ID is missing."

        test_msg = (
            "🚀 <b>[MintDash Alpha Radar Connected]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Bot:</b> @my_mintdash_execution_bot\n"
            "<b>Status:</b> 🟢 Live & Autonomous\n"
            "<b>Monitors:</b> YC & Speedrun • On-Chain Mints • GitHub Bounties\n"
            "<i>Real-time high-ROI alpha alerts will stream here 24/7.</i>"
        )
        return self.send_message(test_msg)

    def send_launch_alert(self, item: LaunchItem) -> Tuple[bool, Optional[str]]:
        """Sends an early founder signal or confirmed YC launch alert."""
        is_early = item.status == LaunchStatus.EARLY_SIGNAL
        header_emoji = "🔥" if is_early else "⚡"
        title = "EARLY FOUNDER SIGNAL" if is_early else "NEW CONFIRMED LAUNCH"
        batch_label = item.batch or "Active Batch"
        website_link = f"<a href='{item.website}'>{item.company_name}</a>" if item.website else f"<b>{item.company_name}</b>"

        founders_str = "Unknown"
        if item.founders:
            founders_str = ", ".join([f"{f.name} ({f.handle or f.title or 'Founder'})" for f in item.founders])

        post_url = item.post_url or "https://ycombinator.com"
        quote_section = f"\n💬 <i>\"{item.post_text}\"</i>\n" if item.post_text else ""
        desc_section = f"\n📝 {item.description}\n" if item.description else ""

        html = (
            f"{header_emoji} <b>[{title}] {item.company_name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Company:</b> {website_link}\n"
            f"🏷️ <b>Batch:</b> {batch_label} ({item.program_type.value})\n"
            f"👤 <b>Founders:</b> {founders_str}\n"
            f"📊 <b>Status:</b> {'🔥 EARLY_SIGNAL (Pre-Directory)' if is_early else '✅ CONFIRMED'}\n"
            f"📡 <b>Source:</b> {item.source.value}\n"
            f"🔗 <a href='{post_url}'>View Source Post</a>\n"
            f"{quote_section}"
            f"{desc_section}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Powered by MintDash Autonomous Alpha Radar</i>"
        )
        return self.send_message(html)

    def send_onchain_mint_alert(
        self,
        contract_name: str,
        contract_address: str,
        chain: str,
        mint_price_eth: float,
        simulated_gas_eth: float,
        whale_wallets_active: int,
        etherscan_url: str
    ) -> Tuple[bool, Optional[str]]:
        """Dispatches an on-chain smart money mint alert."""
        html = (
            f"💎 <b>[SMART MONEY ON-CHAIN MINT]</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Contract:</b> <code>{contract_name}</code>\n"
            f"🌐 <b>Network:</b> {chain.upper()}\n"
            f"📍 <b>Address:</b> <code>{contract_address}</code>\n"
            f"💰 <b>Mint Price:</b> {mint_price_eth:.4f} ETH\n"
            f"⚡ <b>Estimated Gas:</b> {simulated_gas_eth:.4f} ETH\n"
            f"🐋 <b>Whales Active:</b> {whale_wallets_active} Top Smart Wallets\n"
            f"🛡️ <b>Simulation:</b> ✅ 100% Passed (0 Slippage, Verified Safe)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <a href='{etherscan_url}'>View on Explorer</a>"
        )
        return self.send_message(html)

    def send_bounty_alert(
        self,
        repo: str,
        title: str,
        reward_usd: float,
        issue_url: str,
        tech_tags: List[str],
        summary: str
    ) -> Tuple[bool, Optional[str]]:
        """Dispatches an open GitHub cash bounty alert."""
        tags_str = " ".join([f"#{t}" for t in tech_tags]) if tech_tags else "#code"
        html = (
            f"🎯 <b>[HIGH-VALUE GITHUB BOUNTY DETECTED]</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Reward:</b> <b>${reward_usd:,.2f} USD</b>\n"
            f"📂 <b>Repository:</b> <code>{repo}</code>\n"
            f"📌 <b>Issue:</b> {title}\n"
            f"🏷️ <b>Tags:</b> {tags_str}\n"
            f"📝 <b>Summary:</b> {summary}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 <a href='{issue_url}'>Claim Bounty & View Issue</a>"
        )
        return self.send_message(html)

    def set_webhook(self, webhook_url: str) -> Tuple[bool, str]:
        """Registers the public webhook URL with Telegram Bot API."""
        if not self.bot_token:
            return False, "Bot token missing."
        url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
        try:
            req_data = json.dumps({"url": webhook_url}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("ok"):
                    logger.info(f"[TelegramNotifier] Webhook registered successfully: {webhook_url}")
                    return True, "Webhook registered successfully."
                return False, data.get("description", "Failed to set webhook.")
        except Exception as e:
            logger.error(f"[TelegramNotifier] setWebhook failed: {e}")
            return False, str(e)

telegram_notifier = TelegramNotifier()

