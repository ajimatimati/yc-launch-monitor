import sqlite3
import json
import logging
import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .models import LaunchItem, LaunchStatus, LaunchSource, ProgramType, FounderInfo, DatabaseStats
from .config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        else:
            # Ensure parent directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._mem_conn:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes database tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table: launches
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS launches (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                slug TEXT,
                website TEXT,
                batch TEXT,
                program_type TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                founders_json TEXT,
                description TEXT,
                post_text TEXT,
                post_url TEXT,
                detected_at TIMESTAMP NOT NULL,
                confirmed_at TIMESTAMP,
                slack_sent INTEGER DEFAULT 0,
                slack_ts TEXT,
                metadata_json TEXT
            );
            """)

            # Table: scan_history
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                scanned_at TIMESTAMP NOT NULL,
                items_found INTEGER NOT NULL,
                new_items_count INTEGER NOT NULL,
                error_message TEXT,
                duration_seconds REAL
            );
            """)

            # Table: idempotency_store (for Pond API runs)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_store (
                run_id TEXT PRIMARY KEY,
                action_id TEXT,
                parameters_json TEXT,
                response_json TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
            """)

            # Table: app_config (key-value settings vault)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
            """)

            # Create Indexes for fast lookup & deduplication
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_launches_company ON launches(company_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_launches_slug ON launches(slug);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_launches_status ON launches(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_launches_batch ON launches(batch);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_launches_detected ON launches(detected_at);")

            conn.commit()

    def get_by_id(self, launch_id: str) -> Optional[LaunchItem]:
        """Retrieves a launch item by its unique ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM launches WHERE id = ?", (launch_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_launch_item(row)
        return None

    def find_existing_company(self, company_name: str, slug: Optional[str] = None) -> Optional[LaunchItem]:
        """Looks up an existing company by canonical name or slug to handle deduplication and status transitions."""
        clean_name = company_name.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if slug:
                cursor.execute("SELECT * FROM launches WHERE slug = ? OR lower(company_name) = ? LIMIT 1", (slug, clean_name))
            else:
                cursor.execute("SELECT * FROM launches WHERE lower(company_name) = ? LIMIT 1", (clean_name,))
            row = cursor.fetchone()
            if row:
                return self._row_to_launch_item(row)
        return None

    def save_launch(self, item: LaunchItem) -> Tuple[bool, bool]:
        """
        Saves a launch item.
        Returns:
            (is_new, status_upgraded_to_confirmed)
        """
        existing = self.find_existing_company(item.company_name, item.slug)
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if existing is None:
                # Completely new item
                founders_str = json.dumps([f.model_dump() for f in item.founders])
                metadata_str = json.dumps(item.metadata)
                
                cursor.execute("""
                INSERT INTO launches (
                    id, company_name, slug, website, batch, program_type, source,
                    status, founders_json, description, post_text, post_url,
                    detected_at, confirmed_at, slack_sent, slack_ts, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
                """, (
                    item.id,
                    item.company_name,
                    item.slug,
                    item.website,
                    item.batch,
                    item.program_type.value,
                    item.source.value,
                    item.status.value,
                    founders_str,
                    item.description,
                    item.post_text,
                    item.post_url,
                    item.detected_at.isoformat(),
                    item.confirmed_at.isoformat() if item.confirmed_at else None,
                    metadata_str
                ))
                conn.commit()
                return True, False

            # Existing item found: check if this is an upgrade from EARLY_SIGNAL -> CONFIRMED
            if existing.status == LaunchStatus.EARLY_SIGNAL and item.status == LaunchStatus.CONFIRMED:
                # Update status to CONFIRMED and augment metadata
                confirmed_at_iso = now_utc.isoformat()
                founders_str = json.dumps([f.model_dump() for f in (item.founders or existing.founders)])
                
                # Merge metadata
                merged_meta = existing.metadata.copy()
                merged_meta.update(item.metadata)
                merged_meta["early_detected_at"] = existing.detected_at.isoformat()
                
                cursor.execute("""
                UPDATE launches SET
                    status = ?,
                    confirmed_at = ?,
                    slug = COALESCE(?, slug),
                    website = COALESCE(?, website),
                    batch = COALESCE(?, batch),
                    description = COALESCE(?, description),
                    founders_json = ?,
                    metadata_json = ?
                WHERE id = ?
                """, (
                    LaunchStatus.CONFIRMED.value,
                    confirmed_at_iso,
                    item.slug,
                    item.website,
                    item.batch,
                    item.description,
                    founders_str,
                    json.dumps(merged_meta),
                    existing.id
                ))
                conn.commit()
                return False, True

            # Already exists and no upgrade needed (deduplicated)
            return False, False

    def mark_slack_sent(self, launch_id: str, slack_ts: Optional[str] = None):
        """Marks a launch as having had its Slack alert successfully delivered."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE launches SET slack_sent = 1, slack_ts = ? WHERE id = ?", (slack_ts, launch_id))
            conn.commit()

    def record_scan_history(self, source: LaunchSource, items_found: int, new_items_count: int, error_message: Optional[str] = None, duration_sec: float = 0.0):
        """Logs the completion of a monitoring pass."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO scan_history (source, scanned_at, items_found, new_items_count, error_message, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source.value,
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                items_found,
                new_items_count,
                error_message,
                duration_sec
            ))
            conn.commit()

    def get_stats(self) -> DatabaseStats:
        """Calculates operational statistics from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM launches")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM launches WHERE status = ?", (LaunchStatus.EARLY_SIGNAL.value,))
            early = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM launches WHERE status = ?", (LaunchStatus.CONFIRMED.value,))
            confirmed = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM launches WHERE program_type = ?", (ProgramType.SPEEDRUN.value,))
            speedrun = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM launches WHERE program_type = ?", (ProgramType.YC.value,))
            yc = cursor.fetchone()[0]

            cursor.execute("SELECT scanned_at FROM scan_history ORDER BY id DESC LIMIT 1")
            last_scan_row = cursor.fetchone()
            last_scan = last_scan_row[0] if last_scan_row else None

            return DatabaseStats(
                total_tracked_companies=total,
                early_signal_count=early,
                confirmed_count=confirmed,
                speedrun_count=speedrun,
                yc_count=yc,
                last_scan_time=last_scan
            )

    def list_launches(self, limit: int = 50, status: Optional[LaunchStatus] = None, query: Optional[str] = None) -> List[LaunchItem]:
        """Lists launches filtered by status or query keyword."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM launches WHERE 1=1"
            params = []

            if status:
                sql += " AND status = ?"
                params.append(status.value)
            
            if query:
                sql += " AND (company_name LIKE ? OR batch LIKE ? OR description LIKE ? OR post_text LIKE ?)"
                wildcard = f"%{query}%"
                params.extend([wildcard, wildcard, wildcard, wildcard])

            sql += " ORDER BY detected_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_launch_item(row) for row in rows]

    # Pond Protocol Idempotency Cache
    def get_idempotent_response(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT response_json FROM idempotency_store WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def save_idempotent_response(self, run_id: str, action_id: Optional[str], parameters: Dict[str, Any], response_data: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO idempotency_store (run_id, action_id, parameters_json, response_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (
                run_id,
                action_id,
                json.dumps(parameters),
                json.dumps(response_data),
                datetime.datetime.now(datetime.timezone.utc).isoformat()
            ))
            conn.commit()

    def set_config(self, key: str, value: str):
        """Sets a persistent configuration key-value pair."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO app_config (key, value, updated_at)
            VALUES (?, ?, ?)
            """, (key, value, datetime.datetime.now(datetime.timezone.utc).isoformat()))
            conn.commit()

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Gets a persistent configuration value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default

    def _row_to_launch_item(self, row: sqlite3.Row) -> LaunchItem:
        founders_raw = json.loads(row["founders_json"]) if row["founders_json"] else []
        founders = [FounderInfo(**f) for f in founders_raw]
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        
        detected_dt = datetime.datetime.fromisoformat(row["detected_at"])
        confirmed_dt = datetime.datetime.fromisoformat(row["confirmed_at"]) if row["confirmed_at"] else None

        return LaunchItem(
            id=row["id"],
            company_name=row["company_name"],
            slug=row["slug"],
            website=row["website"],
            batch=row["batch"],
            program_type=ProgramType(row["program_type"]),
            source=LaunchSource(row["source"]),
            status=LaunchStatus(row["status"]),
            founders=founders,
            description=row["description"],
            post_text=row["post_text"],
            post_url=row["post_url"],
            detected_at=detected_dt,
            confirmed_at=confirmed_dt,
            metadata=metadata
        )

# Global database manager instance
db = DatabaseManager()
