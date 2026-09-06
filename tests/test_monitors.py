import pytest
from yc_launch_monitor.monitors.yc_directory import YCDirectoryMonitor
from yc_launch_monitor.monitors.speedrun_directory import SpeedrunDirectoryMonitor
from yc_launch_monitor.monitors.x_twitter import XTwitterMonitor
from yc_launch_monitor.monitors.linkedin import LinkedInMonitor
from yc_launch_monitor.models import LaunchStatus, ProgramType, LaunchSource

def test_yc_directory_algolia_parsing():
    monitor = YCDirectoryMonitor()
    raw_hit = {
        "id": 12345,
        "name": "Talos",
        "slug": "talos-us",
        "website": "https://www.talos-us.com/",
        "batch": "Fall 2026",
        "one_liner": "Predictive maintenance for power infrastructure.",
        "all_locations": "Baltimore, MD, USA",
        "team_size": 3,
        "launched_at": 1787763466
    }
    
    item = monitor._parse_algolia_hit(raw_hit)
    assert item is not None
    assert item.company_name == "Talos"
    assert item.slug == "talos-us"
    assert item.batch == "Fall 2026"
    assert item.status == LaunchStatus.CONFIRMED
    assert item.program_type == ProgramType.YC
    assert item.website == "https://www.talos-us.com/"

def test_speedrun_api_parsing():
    monitor = SpeedrunDirectoryMonitor()
    raw_comp = {
        "id": "sr-uuid-001",
        "name": "Acceler8",
        "slug": "acceler8",
        "website_url": "https://useacceler8.com",
        "cohort": "SR006",
        "preamble": "AI for Workforce Intelligence & Planning",
        "industries": ["HR Tech", "AI Agents"],
        "founder_set": [
            {"first_name": "Chinmay", "last_name": "Chauhan", "title": "Co-Founder", "linkedin_url": "https://linkedin.com/in/chinmay"}
        ]
    }

    item = monitor._parse_speedrun_company(raw_comp)
    assert item is not None
    assert item.company_name == "Acceler8"
    assert item.batch == "SR006"
    assert item.program_type == ProgramType.SPEEDRUN
    assert item.status == LaunchStatus.CONFIRMED
    assert len(item.founders) == 1
    assert item.founders[0].name == "Chinmay Chauhan"

def test_x_twitter_early_signal_extraction():
    monitor = XTwitterMonitor()
    text = "We got into YC S26! Excited to move to SF and start building https://acme.ai with Jane Doe."
    
    item = monitor._extract_launch_from_tweet(
        tweet_id="2061493360150601738",
        text=text,
        author_name="Beknazar Abdikamalov",
        author_handle="beknabdik"
    )

    assert item is not None
    assert item.status == LaunchStatus.EARLY_SIGNAL
    assert item.source == LaunchSource.X_TWITTER
    assert item.program_type == ProgramType.YC
    assert "YC S26" in item.batch
    assert item.founders[0].handle == "@beknabdik"
    assert "2061493360150601738" in item.post_url

def test_linkedin_early_signal_extraction():
    monitor = LinkedInMonitor()
    text = "Alexei Romanov on LinkedIn: I'm proud to share that Synapse Flow has officially been accepted into the Y Combinator S26 batch!"
    
    item = monitor._extract_launch_from_linkedin_text(
        post_id="post_99999",
        text=text,
        url="https://linkedin.com/posts/alexei-romanov-activity-123"
    )

    assert item is not None
    assert item.status == LaunchStatus.EARLY_SIGNAL
    assert item.source == LaunchSource.LINKEDIN
    assert item.program_type == ProgramType.YC
    assert item.founders[0].name == "Alexei Romanov"

def test_early_signal_links_are_valid():
    """Verifies that early signal crawler returns items with valid, non-broken links."""
    monitor = XTwitterMonitor()
    items = monitor.scan(limit=10)
    assert len(items) > 0
    for itm in items:
        assert itm.status == LaunchStatus.EARLY_SIGNAL
        assert itm.post_url is not None
        assert itm.post_url.startswith("http")
        if itm.website:
            assert itm.website.startswith("http")
        # Ensure no synthetic placeholder domains
        for forbidden in ["hyperscale.ai", "kallisto.bio", "synapseflow.dev", "aurapayments.io"]:
            assert forbidden not in str(itm.website)
            assert forbidden not in str(itm.post_url)
