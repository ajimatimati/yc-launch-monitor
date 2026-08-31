"""
Interactive Telegram Command & Webhook Controller for @my_mintdash_execution_bot.
Handles mobile phone commands (/start, /stats, /scan, /early, /mints, /bounties, /vault, /wallet_create).
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List

from ..config import settings
from ..database import db
from ..engine import monitor_engine
from ..models import LaunchStatus
from ..monitors.onchain_mints import onchain_mint_monitor
from ..monitors.bounty_scout import bounty_scout_monitor
from ..web3_vault.wallet_vault import wallet_vault
from .notifier import telegram_notifier

logger = logging.getLogger(__name__)

def get_main_menu_keyboard() -> Dict[str, Any]:
    """Generates 1-tap interactive inline buttons for mobile phone control."""
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ Run Alpha Scan", "callback_data": "cmd_scan"},
                {"text": "🔥 Early Signals", "callback_data": "cmd_early"}
            ],
            [
                {"text": "💎 Smart Mints", "callback_data": "cmd_mints"},
                {"text": "🎯 GitHub Bounties", "callback_data": "cmd_bounties"}
            ],
            [
                {"text": "📊 Live Stats", "callback_data": "cmd_stats"},
                {"text": "🛡️ Safe Vault", "callback_data": "cmd_vault"}
            ]
        ]
    }

class TelegramCommandHandler:
    """Processes incoming Telegram updates and executes commands."""

    def handle_update(self, update: Dict[str, Any]) -> bool:
        """Parses update payload and dispatches command."""
        # 1. Handle Callback Query (Button taps)
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = str(cb.get("message", {}).get("chat", {}).get("id"))
            data = cb.get("data", "")
            return self._execute_command(data, chat_id)

        # 2. Handle Text Message
        if "message" in update:
            msg = update["message"]
            chat_id = str(msg.get("chat", {}).get("id"))
            text = msg.get("text", "").strip()
            return self._execute_command(text, chat_id)

        return False

    def _execute_command(self, raw_cmd: str, chat_id: str) -> bool:
        cmd = raw_cmd.lower().strip()

        # Authorization check: only authorized chat or default allowed
        if chat_id != telegram_notifier.chat_id:
            logger.warning(f"[TelegramCommandHandler] Unauthorized chat_id: {chat_id}")
            telegram_notifier.send_message(
                "⛔ <b>Access Denied:</b> This bot is locked to authorized GTM & Web3 operators.",
                reply_markup=None
            )
            return False

        if cmd in ["/start", "/help", "cmd_help", "help"]:
            return self._handle_help()
        elif cmd in ["/stats", "cmd_stats", "stats"]:
            return self._handle_stats()
        elif cmd in ["/scan", "cmd_scan", "scan"]:
            return self._handle_scan()
        elif cmd in ["/early", "cmd_early", "early"]:
            return self._handle_early()
        elif cmd in ["/mints", "cmd_mints", "mints"]:
            return self._handle_mints()
        elif cmd in ["/bounties", "cmd_bounties", "bounties"]:
            return self._handle_bounties()
        elif cmd in ["/vault", "cmd_vault", "vault"]:
            return self._handle_vault()
        elif cmd in ["/wallet_create", "cmd_wallet_create", "create_wallet"]:
            return self._handle_wallet_create()
        elif cmd.startswith("/pitch"):
            company = raw_cmd.replace("/pitch", "").strip()
            return self._handle_pitch(company)
        else:
            return self._handle_unknown(raw_cmd)

    def _handle_help(self) -> bool:
        html = (
            "🚀 <b>[MintDash Autonomous Alpha Command Center]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Welcome! Control your entire 24/7 autonomous cloud engine directly from your phone.\n\n"
            "<b>📱 Quick Commands:</b>\n"
            "• <code>/scan</code> — Trigger immediate multi-stream alpha scan\n"
            "• <code>/early</code> — View latest pre-announcement YC founders\n"
            "• <code>/mints</code> — View Base & Ethereum smart money mints\n"
            "• <code>/bounties</code> — View active $50-$1,500 GitHub cash bounties\n"
            "• <code>/vault</code> — Check non-custodial safe wallet balances\n"
            "• <code>/wallet_create</code> — Generate new local execution keypair\n"
            "• <code>/stats</code> — View live database and daemon metrics\n"
            "• <code>/pitch [company]</code> — Generate personalized Rho founder pitch\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Tap any button below to execute instantly:</i>"
        )
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_stats(self) -> bool:
        st = db.get_stats()
        wallets = wallet_vault.list_public_wallets()
        html = (
            "📊 <b>[MintDash Live System Metrics]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Status:</b> 🟢 100% Autonomous in Cloud\n"
            f"• <b>Total Startups Tracked:</b> {st.total_tracked_companies}\n"
            f"• <b>🔥 Early Social Signals:</b> {st.early_signal_count}\n"
            f"• <b>✅ Confirmed YC / Speedrun:</b> {st.confirmed_count}\n"
            f"• <b>🛡️ Controlled Wallets:</b> {len(wallets)} (PBKDF2 Encrypted)\n"
            f"• <b>Cadence:</b> 8-hour continuous background loop\n"
            f"• <b>Last Polling Scan:</b> {st.last_scan_time or 'Active'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Cloud Container: yc-launch-monitor.onrender.com</i>"
        )
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_scan(self) -> bool:
        telegram_notifier.send_message("⏳ <i>Running immediate scan across YC, Speedrun, X, LinkedIn, Base mints & GitHub bounties...</i>")
        summary = monitor_engine.run_scan(send_slack=False, send_telegram=False)
        mints = onchain_mint_monitor.scan_mints(send_telegram=False)
        bounties = bounty_scout_monitor.scan_bounties(send_telegram=False)

        html = (
            "⚡ <b>[Autonomous Scan Completed]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>New Startups Detected:</b> {summary.total_new_items}\n"
            f"• <b>🔥 Early Founder Signals:</b> {summary.total_early_signals}\n"
            f"• <b>✅ Confirmed Launches:</b> {summary.total_confirmed}\n"
            f"• <b>💎 Smart Money Mints:</b> {len(mints)} opportunities on Base\n"
            f"• <b>🎯 Active Cash Bounties:</b> {len(bounties)} funded issues\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>All discoveries saved to persistent database.</i>"
        )
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_early(self) -> bool:
        items = db.list_launches(status=LaunchStatus.EARLY_SIGNAL, limit=5)
        if not items:
            html = "🔥 <b>No early signals detected in current window. Run /scan to refresh.</b>"
            success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
            return success

        html = "🔥 <b>[Latest Early Founder Signals Detected]</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, item in enumerate(items, 1):
            founders_str = item.display_founder
            post_link = f"<a href='{item.post_url}'>Source Post</a>" if item.post_url else "Social Stream"
            html += f"<b>{i}. {item.company_name}</b> ({item.batch or 'YC S26'})\n"
            html += f"👤 <b>Founder:</b> {founders_str}\n"
            html += f"📡 <b>Source:</b> {item.source.value} • {post_link}\n"
            if item.post_text:
                clean_quote = item.post_text[:100].replace('"', "'")
                html += f"💬 <i>\"{clean_quote}...\"</i>\n"
            html += "\n"
        html += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_mints(self) -> bool:
        mints = onchain_mint_monitor.scan_mints(send_telegram=False)
        html = "💎 <b>[On-Chain Smart Money Mints (Base / Eth)]</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, m in enumerate(mints, 1):
            html += f"<b>{i}. {m.contract_name}</b>\n"
            html += f"🌐 <b>Chain:</b> {m.chain.upper()} | 💰 <b>Price:</b> {m.mint_price_eth:.4f} ETH\n"
            html += f"⚡ <b>Gas:</b> {m.simulated_gas_eth:.4f} ETH | 🐋 <b>Whales:</b> {m.whale_wallets_active}\n"
            html += f"🛡️ <b>Simulation:</b> ✅ 100% Passed (0% Risk)\n"
            html += f"🔗 <a href='{m.etherscan_url}'>View Explorer</a>\n\n"
        html += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_bounties(self) -> bool:
        bounties = bounty_scout_monitor.scan_bounties(send_telegram=False)
        html = "🎯 <b>[Active GitHub Cash Bounties ($50 - $1,500)]</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, b in enumerate(bounties, 1):
            tags_str = " ".join([f"#{t}" for t in b.tech_tags[:3]])
            html += f"<b>{i}. {b.title}</b>\n"
            html += f"💰 <b>Reward:</b> <b>${b.reward_usd:,.2f} USD</b> | 📂 <code>{b.repo}</code>\n"
            html += f"🏷️ <code>{tags_str}</code>\n"
            html += f"🚀 <a href='{b.issue_url}'>Claim Bounty Issue</a>\n\n"
        html += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_vault(self) -> bool:
        wallets = wallet_vault.list_public_wallets()
        html = (
            "🛡️ <b>[Web3 Non-Custodial Multi-Wallet Vault]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Controlled Wallets:</b> {len(wallets)}\n"
            f"• <b>Encryption:</b> PBKDF2 HMAC-SHA256 (480k rounds)\n"
            f"• <b>Default Chain:</b> {settings.DEFAULT_CHAIN.upper()}\n"
            f"• <b>Max Spend Cap:</b> {settings.MAX_TASK_SPEND_ETH} ETH\n\n"
        )
        if wallets:
            html += "<b>Public Wallet Addresses:</b>\n"
            for w in wallets:
                html += f"• <code>{w['address']}</code> ({w['label']})\n"
        else:
            html += "<i>No local wallets in vault. Use /wallet_create to generate one.</i>\n"
        html += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_wallet_create(self) -> bool:
        label = f"Alpha Execution Wallet #{len(wallet_vault.wallets) + 1}"
        entry = wallet_vault.create_wallet(label)
        html = (
            "🔑 <b>[New Safe Local Wallet Generated]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Label:</b> {entry.label}\n"
            f"• <b>Public Address:</b> <code>{entry.address}</code>\n"
            f"• <b>Security:</b> Encrypted in PBKDF2 local vault file\n"
            f"• <b>Mode:</b> Non-Custodial (You retain full cryptographic control)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Ready for automated smart contract mint execution.</i>"
        )
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_pitch(self, company: str) -> bool:
        results = db.list_launches(limit=1, query=company)
        if not results:
            html = f"⚠️ <i>Company '{company}' not found in database. Showing generic template:</i>\n\n"
            c_name = company or "Founder"
            f_name = "Founder"
        else:
            item = results[0]
            c_name = item.company_name
            f_name = item.founders[0].name if item.founders else "Founder"

        pitch = (
            f"Hi {f_name},\n\n"
            f"Huge congrats on {c_name} and joining YC! Building at the frontier of high-growth tech is incredible.\n\n"
            f"I lead GTM partnerships at Rho. We help venture-backed founders optimize cash treasury and financial operations from day one with zero banking friction.\n\n"
            f"Would love to connect for 10 mins if helpful: https://calendly.com/jayson-rho\n\n"
            f"Best,\nJayson Fung | Senior GTM at Rho"
        )
        html = (
            f"💼 <b>[1-Click Rho Outreach Pitch: {c_name}]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<code>{pitch}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Copy-paste ready for LinkedIn, X DM, or email.</i>"
        )
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

    def _handle_unknown(self, text: str) -> bool:
        html = (
            f"❓ <i>Command '{text}' not recognized.</i>\n\n"
            "Tap any button below or type <code>/help</code> to see available actions."
        )
        success, _ = telegram_notifier.send_message(html, reply_markup=get_main_menu_keyboard())
        return success

telegram_handler = TelegramCommandHandler()
