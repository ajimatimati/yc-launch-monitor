import json
import logging
import datetime
import requests
from typing import List, Dict, Any, Optional

from .base import BaseMonitor
from ..models import LaunchItem, LaunchSource, LaunchStatus, ProgramType, FounderInfo

logger = logging.getLogger(__name__)

class SpeedrunDirectoryMonitor(BaseMonitor):
    """
    Monitors the Speedrun accelerator directory (https://speedrun.a16z.com/companies/).
    Extracts cohort batches (e.g. SR005, SR006, SR007), company details, and founder rosters.
    """

    SPEEDRUN_API_URL = "https://speedrun-api.a16z.com/api/companies/companies/"

    @property
    def source_name(self) -> LaunchSource:
        return LaunchSource.SPEEDRUN_DIRECTORY

    @property
    def program_type(self) -> ProgramType:
        return ProgramType.SPEEDRUN

    def scan(self, limit: int = 50) -> List[LaunchItem]:
        """Fetches newly announced or listed Speedrun companies."""
        logger.info("Scanning Speedrun Directory API...")
        items: List[LaunchItem] = []

        try:
            headers = {
                "User-Agent": "SpeedrunMonitor/1.0 (Rho GTM Pipeline Radar)",
                "Accept": "application/json"
            }
            params = {
                "limit": min(limit, 50),
                "offset": 0
            }

            resp = requests.get(self.SPEEDRUN_API_URL, headers=headers, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            for res in results:
                item = self._parse_speedrun_company(res)
                if item:
                    items.append(item)

            logger.info(f"Successfully fetched {len(items)} companies from Speedrun Directory.")
            return items

        except Exception as e:
            logger.error(f"Error querying Speedrun API: {e}. Attempting Next.js SSR fallback...")
            return self._scrape_nextjs_fallback(limit)

    def _parse_speedrun_company(self, c: Dict[str, Any]) -> Optional[LaunchItem]:
        try:
            name = c.get("name")
            if not name:
                return None

            slug = c.get("slug") or name.lower().replace(" ", "-")
            cohort = c.get("cohort") or "Speedrun"
            website = c.get("website_url")
            desc = c.get("preamble") or c.get("description") or ""

            # Parse founders
            founders: List[FounderInfo] = []
            for f in c.get("founder_set", []):
                fname = f"{f.get('first_name', '')} {f.get('last_name', '')}".strip()
                ftitle = f.get("title")
                flink = f.get("linkedin_url")
                if fname:
                    founders.append(FounderInfo(name=fname, title=ftitle, profile_url=flink))

            profile_url = f"https://speedrun.a16z.com/companies/{slug}"

            return LaunchItem(
                id=f"speedrun_{c.get('id', slug)}",
                company_name=name,
                slug=slug,
                website=website,
                batch=cohort,
                program_type=ProgramType.SPEEDRUN,
                source=LaunchSource.SPEEDRUN_DIRECTORY,
                status=LaunchStatus.CONFIRMED,
                founders=founders,
                description=desc,
                post_url=profile_url,
                detected_at=datetime.datetime.now(datetime.timezone.utc),
                confirmed_at=datetime.datetime.now(datetime.timezone.utc),
                metadata={
                    "cohort": cohort,
                    "industries": c.get("industries", []),
                    "city": c.get("city"),
                    "state": c.get("state"),
                    "country": c.get("country"),
                    "team_size": c.get("team_size"),
                    "logo_url": c.get("logo"),
                    "x_url": c.get("x_url"),
                    "linkedin_url": c.get("linkedin_url"),
                    "speedrun_profile_url": profile_url
                }
            )
        except Exception as e:
            logger.warning(f"Failed to parse Speedrun company object: {e}")
            return None

    def _scrape_nextjs_fallback(self, limit: int) -> List[LaunchItem]:
        """Next.js SSR __NEXT_DATA__ scraper fallback."""
        try:
            from bs4 import BeautifulSoup
            url = "https://speedrun.a16z.com/companies/"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if not script_tag:
                return []

            next_data = json.loads(script_tag.string)
            companies = next_data.get("props", {}).get("pageProps", {}).get("companies", {}).get("results", [])
            
            items = []
            for c in companies[:limit]:
                item = self._parse_speedrun_company(c)
                if item:
                    items.append(item)
            return items
        except Exception as e:
            logger.error(f"Speedrun Next.js fallback failed: {e}")
            return []
