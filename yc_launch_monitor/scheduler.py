import time
import logging
import threading
import datetime
from typing import Optional

from .engine import monitor_engine
from .config import settings

logger = logging.getLogger(__name__)

class ContinuousScheduler:
    """
    Background continuous scheduler that triggers incremental scans on an 8-hour cadence
    (or user-configured interval in settings).
    """

    def __init__(self, interval_hours: Optional[int] = None):
        self.interval_seconds = (interval_hours or settings.POLL_INTERVAL_HOURS) * 3600
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, run_immediately: bool = True):
        """Starts the background continuous monitoring loop."""
        if self._running:
            logger.warning("Continuous scheduler is already running.")
            return

        self._running = True
        logger.info(f"Starting Continuous Scheduler with interval of {settings.POLL_INTERVAL_HOURS} hours ({self.interval_seconds}s)...")
        
        self._thread = threading.Thread(target=self._run_loop, args=(run_immediately,), daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the continuous monitoring loop."""
        logger.info("Stopping Continuous Scheduler...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _run_loop(self, run_immediately: bool):
        if run_immediately:
            try:
                logger.info("Triggering initial automated monitoring scan...")
                monitor_engine.run_scan(send_slack=True)
            except Exception as e:
                logger.error(f"Error during initial automated scan: {e}")

        while self._running:
            # Sleep in short increments to allow prompt shutdown
            elapsed = 0
            while self._running and elapsed < self.interval_seconds:
                time.sleep(5)
                elapsed += 5

            if not self._running:
                break

            try:
                logger.info(f"Triggering scheduled 8-hour incremental monitoring scan at {datetime.datetime.now(datetime.timezone.utc).isoformat()}...")
                monitor_engine.run_scan(send_slack=True)
            except Exception as e:
                logger.error(f"Error during scheduled monitoring scan: {e}", exc_info=True)

# Global scheduler instance
scheduler = ContinuousScheduler()
