import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ProgramType(str, Enum):
    YC = "YC"
    SPEEDRUN = "SPEEDRUN"

class LaunchSource(str, Enum):
    YC_DIRECTORY = "YC_DIRECTORY"
    SPEEDRUN_DIRECTORY = "SPEEDRUN_DIRECTORY"
    X_TWITTER = "X_TWITTER"
    LINKEDIN = "LINKEDIN"

class LaunchStatus(str, Enum):
    EARLY_SIGNAL = "EARLY_SIGNAL"  # Founder announced on social media before YC official directory
    CONFIRMED = "CONFIRMED"        # Officially listed on YC or Speedrun directory

class FounderInfo(BaseModel):
    name: Optional[str] = None
    handle: Optional[str] = None
    profile_url: Optional[str] = None
    title: Optional[str] = None

class LaunchItem(BaseModel):
    # Unique identifier (e.g. hash of company name / slug or post URL)
    id: str
    company_name: str
    slug: Optional[str] = None
    website: Optional[str] = None
    batch: Optional[str] = None  # e.g. "YC S26", "YC W26", "SR006"
    program_type: ProgramType = ProgramType.YC
    source: LaunchSource
    status: LaunchStatus = LaunchStatus.CONFIRMED
    
    founders: List[FounderInfo] = Field(default_factory=list)
    description: Optional[str] = None
    post_text: Optional[str] = None
    post_url: Optional[str] = None
    
    detected_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    confirmed_at: Optional[datetime.datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def display_founder(self) -> str:
        if not self.founders:
            return "Founder"
        f = self.founders[0]
        if f.name and f.handle:
            return f"{f.name} (@{f.handle.lstrip('@')})"
        return f.name or f.handle or "Founder"

    @property
    def primary_link(self) -> str:
        if self.post_url:
            return self.post_url
        if self.website:
            return self.website
        if self.slug:
            return f"https://www.ycombinator.com/companies/{self.slug}"
        return "https://www.ycombinator.com/companies"

class SourceScanResult(BaseModel):
    source: LaunchSource
    items: List[LaunchItem] = Field(default_factory=list)
    total_found: int = 0
    new_items_count: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0

class OverallScanSummary(BaseModel):
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    total_new_items: int = 0
    total_early_signals: int = 0
    total_confirmed: int = 0
    results_by_source: Dict[str, SourceScanResult] = Field(default_factory=dict)
    slack_delivered_count: int = 0

class DatabaseStats(BaseModel):
    total_tracked_companies: int
    early_signal_count: int
    confirmed_count: int
    speedrun_count: int
    yc_count: int
    last_scan_time: Optional[str] = None
