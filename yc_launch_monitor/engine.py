import time
import logging
import datetime
from typing import List, Optional, Dict

from .models import (
    LaunchItem,
    LaunchStatus,
    LaunchSource,
    SourceScanResult,
    OverallScanSummary
)
from .database import db
from .slack.notifier import slack_notifier
from .telegram.notifier import telegram_notifier
from .monitors.onchain_mints import onchain_mint_monitor
from .monitors.bounty_scout import bounty_scout_monitor
from .config import settings
from .monitors.base import BaseMonitor
from .monitors.yc_directory import YCDirectoryMonitor
from .monitors.speedrun_directory import SpeedrunDirectoryMonitor
from .monitors.x_twitter import XTwitterMonitor
from .monitors.linkedin import LinkedInMonitor

logger = logging.getLogger(__name__)

class MonitorEngine:
    """
    Central orchestration engine that coordinates data collection across:
    1. YC Directory, Speedrun, X/Twitter, LinkedIn (Early Founder Signals)
    2. On-Chain Smart Money & Free Mints (Base, Ethereum)
    3. GitHub Cash Bounties ($50-$1,500 on Algora/Polar)
    Dispatches real-time alerts to both MintDash Telegram and Slack.
    """

    def __init__(self):
        self.monitors: Dict[str, BaseMonitor] = {}
        self._init_monitors()

    def _init_monitors(self):
        if settings.ENABLE_YC_DIRECTORY:
            self.monitors["yc_directory"] = YCDirectoryMonitor()
        if settings.ENABLE_SPEEDRUN_DIRECTORY:
            self.monitors["speedrun_directory"] = SpeedrunDirectoryMonitor()
        if settings.ENABLE_X_TWITTER:
            self.monitors["x_twitter"] = XTwitterMonitor()
        if settings.ENABLE_LINKEDIN:
            self.monitors["linkedin"] = LinkedInMonitor()

    def run_scan(
        self,
        specific_sources: Optional[List[str]] = None,
        send_slack: bool = True,
        send_telegram: bool = True,
        dry_run: bool = False
    ) -> OverallScanSummary:
        """
        Executes a monitoring pass across all configured sources.
        """
        start_time = time.time()
        summary = OverallScanSummary()
        
        target_monitors = {}
        if specific_sources:
            for s in specific_sources:
                if s in self.monitors:
                    target_monitors[s] = self.monitors[s]
        else:
            target_monitors = self.monitors

        logger.info(f"Starting monitoring scan across {len(target_monitors)} sources...")

        for source_key, monitor in target_monitors.items():
            s_start = time.time()
            res = SourceScanResult(source=monitor.source_name)
            
            try:
                raw_items = monitor.scan()
                res.total_found = len(raw_items)
                new_items_count = 0

                for item in raw_items:
                    # Save to DB with state progression and deduplication
                    is_new, is_upgraded = db.save_launch(item)
                    
                    if is_new or is_upgraded:
                        new_items_count += 1
                        res.items.append(item)
                        
                        if item.status == LaunchStatus.EARLY_SIGNAL:
                            summary.total_early_signals += 1
                        else:
                            summary.total_confirmed += 1

                        # Send Slack alert
                        if send_slack:
                            success, ts = slack_notifier.send_launch_alert(item, dry_run=dry_run)
                            if success:
                                summary.slack_delivered_count += 1
                                db.mark_slack_sent(item.id, ts)

                        # Send MintDash Telegram alert
                        if send_telegram and not dry_run:
                            telegram_notifier.send_launch_alert(item)

                res.new_items_count = new_items_count
                summary.total_new_items += new_items_count

            except Exception as e:
                logger.error(f"Error scanning source {source_key}: {e}", exc_info=True)
                res.error = str(e)
            
            res.duration_seconds = round(time.time() - s_start, 2)
            db.record_scan_history(
                source=monitor.source_name,
                items_found=res.total_found,
                new_items_count=res.new_items_count,
                error_message=res.error,
                duration_sec=res.duration_seconds
            )
            summary.results_by_source[source_key] = res

        # Run On-Chain and Bounty Scans if enabled
        if settings.ENABLE_ONCHAIN_MINTS and not specific_sources:
            try:
                onchain_mint_monitor.scan_mints(send_telegram=send_telegram and not dry_run)
            except Exception as e:
                logger.error(f"Error in on-chain mint scan: {e}")

        if settings.ENABLE_BOUNTY_SCOUT and not specific_sources:
            try:
                bounty_scout_monitor.scan_bounties(send_telegram=send_telegram and not dry_run)
            except Exception as e:
                logger.error(f"Error in bounty scout scan: {e}")

        logger.info(
            f"Monitoring scan completed in {round(time.time() - start_time, 2)}s. "
            f"Found {summary.total_new_items} new items ({summary.total_early_signals} early signals)."
        )
        return summary

# Global engine instance
monitor_engine = MonitorEngine()
