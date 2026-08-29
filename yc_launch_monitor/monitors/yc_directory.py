import json
import logging
import datetime
import requests
from typing import List, Dict, Any, Optional

from .base import BaseMonitor
from ..models import LaunchItem, LaunchSource, LaunchStatus, ProgramType, FounderInfo
from ..config import settings

logger = logging.getLogger(__name__)

class YCDirectoryMonitor(BaseMonitor):
    """
    Monitors Y Combinator's official startup directory (https://www.ycombinator.com/companies).
    Uses YC's public Algolia search index for real-time newly launched batches, with HTML fallback.
    """

    ALGOLIA_APP_ID = "45BWZJ1SGC"
    ALGOLIA_API_KEY = "NzllNTY5MzJiZGM2OTY2ZTQwMDEzOTNhYWZiZGRjODlhYzVkNjBmOGRjNzJiMWM4ZTU0ZDlhYTZjOTJiMjlhMWFuYWx5dGljc1RhZ3M9eWNkYyZyZXN0cmljdEluZGljZXM9WUNDb21wYW55X3Byb2R1Y3Rpb24lMkNZQ0NvbXBhbnlfQnlfTGF1bmNoX0RhdGVfcHJvZHVjdGlvbiZ0YWdGaWx0ZXJzPSU1QiUyMnljZGNfcHVibGljJTIyJTVE"
    ALGOLIA_URL = f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/YCCompany_By_Launch_Date_production/query"

    @property
    def source_name(self) -> LaunchSource:
        return LaunchSource.YC_DIRECTORY

    @property
    def program_type(self) -> ProgramType:
        return ProgramType.YC

    def scan(self, limit: int = 50) -> List[LaunchItem]:
        """Scans YC directory for newly added/launched companies."""
        logger.info("Scanning YC Directory via Algolia index...")
        items: List[LaunchItem] = []
        
        try:
            headers = {
                "X-Algolia-Application-Id": self.ALGOLIA_APP_ID,
                "X-Algolia-API-Key": self.ALGOLIA_API_KEY,
                "Content-Type": "application/json",
                "User-Agent": "YCLaunchMonitor/1.0 (Rho GTM Radar)"
            }
            
            payload = {
                "query": "",
                "hitsPerPage": min(limit, 100),
                "page": 0
            }

            resp = requests.post(self.ALGOLIA_URL, headers=headers, json=payload, timeout=12)
            resp.raise_for_status()
            data = resp.json()

            hits = data.get("hits", [])
            for hit in hits:
                item = self._parse_algolia_hit(hit)
                if item:
                    items.append(item)

            logger.info(f"Successfully fetched {len(items)} companies from YC Directory.")
            return items

        except Exception as e:
            logger.error(f"Error querying YC Directory Algolia endpoint: {e}. Attempting fallback...")
            return self._scrape_html_fallback(limit)

    def _parse_algolia_hit(self, hit: Dict[str, Any]) -> Optional[LaunchItem]:
        try:
            name = hit.get("name")
            if not name:
                return None

            slug = hit.get("slug") or name.lower().replace(" ", "-")
            batch = hit.get("batch") or "YC Current"
            website = hit.get("website")
            one_liner = hit.get("one_liner") or hit.get("long_description") or ""
            
            # Launched timestamp
            launched_at_ts = hit.get("launched_at")
            if launched_at_ts:
                try:
                    detected_at = datetime.datetime.fromtimestamp(launched_at_ts, datetime.timezone.utc)
                except Exception:
                    detected_at = datetime.datetime.now(datetime.timezone.utc)
            else:
                detected_at = datetime.datetime.now(datetime.timezone.utc)

            # Metadata tags & location
            location = hit.get("all_locations")
            team_size = hit.get("team_size")
            tags = hit.get("tags", [])
            industry = hit.get("industry")
            small_logo = hit.get("small_logo_thumb_url")

            yc_profile_url = f"https://www.ycombinator.com/companies/{slug}"

            return LaunchItem(
                id=f"yc_dir_{hit.get('id', slug)}",
                company_name=name,
                slug=slug,
                website=website,
                batch=batch,
                program_type=ProgramType.YC,
                source=LaunchSource.YC_DIRECTORY,
                status=LaunchStatus.CONFIRMED,
                description=one_liner,
                post_url=yc_profile_url,
                detected_at=detected_at,
                confirmed_at=detected_at,
                metadata={
                    "location": location,
                    "team_size": team_size,
                    "tags": tags,
                    "industry": industry,
                    "logo_url": small_logo,
                    "yc_profile_url": yc_profile_url
                }
            )
        except Exception as e:
            logger.warning(f"Failed to parse YC Algolia hit: {e}")
            return None

    def _scrape_html_fallback(self, limit: int) -> List[LaunchItem]:
        """Fallback scraper in case Algolia network request fails."""
        try:
            from bs4 import BeautifulSoup
            url = "https://www.ycombinator.com/companies"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            items = []
            cards = soup.find_all("a", href=lambda h: h and "/companies/" in h)
            
            for card in cards[:limit]:
                name_elem = card.find("span", class_=lambda c: c and "name" in c.lower())
                name = name_elem.text.strip() if name_elem else card.text.strip()
                if not name:
                    continue
                
                slug = card["href"].split("/companies/")[-1].strip("/")
                items.append(
                    LaunchItem(
                        id=f"yc_html_{slug}",
                        company_name=name,
                        slug=slug,
                        program_type=ProgramType.YC,
                        source=LaunchSource.YC_DIRECTORY,
                        status=LaunchStatus.CONFIRMED,
                        post_url=f"https://www.ycombinator.com/companies/{slug}"
                    )
                )
            return items
        except Exception as e:
            logger.error(f"HTML fallback failed: {e}")
            return []
