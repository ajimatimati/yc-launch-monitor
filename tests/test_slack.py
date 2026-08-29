import pytest
import datetime
from yc_launch_monitor.models import LaunchItem, LaunchStatus, LaunchSource, ProgramType, FounderInfo
from yc_launch_monitor.slack.block_kit import SlackBlockBuilder
from yc_launch_monitor.slack.notifier import SlackNotifier

def test_slack_block_builder_early_signal():
    now = datetime.datetime.now(datetime.timezone.utc)
    item = LaunchItem(
        id="x_123",
        company_name="Acme AI",
        slug="acme-ai",
        website="https://acme.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[FounderInfo(name="Jane Doe", handle="@janedoe", profile_url="https://x.com/janedoe")],
        post_text="We got into YC S26! Excited to move to SF and start building.",
        post_url="https://x.com/janedoe/status/123",
        detected_at=now
    )

    payload = SlackBlockBuilder.build_alert_payload(item)
    assert "EARLY YC SIGNAL" in payload["text"]
    assert len(payload["blocks"]) > 3
    
    # Check header
    header = payload["blocks"][0]
    assert header["type"] == "header"
    assert "EARLY YC SIGNAL" in header["text"]["text"]

    # Check that interactive buttons exist
    actions = [b for b in payload["blocks"] if b.get("type") == "actions"]
    assert len(actions) == 1
    assert len(actions[0]["elements"]) >= 1

def test_slack_block_builder_confirmed_speedrun():
    now = datetime.datetime.now(datetime.timezone.utc)
    item = LaunchItem(
        id="sr_456",
        company_name="Vortix",
        slug="vortix",
        website="https://vortix.tech",
        batch="SR006",
        program_type=ProgramType.SPEEDRUN,
        source=LaunchSource.SPEEDRUN_DIRECTORY,
        status=LaunchStatus.CONFIRMED,
        description="Foundation vision-language-action models for robotics.",
        detected_at=now
    )

    payload = SlackBlockBuilder.build_alert_payload(item)
    assert "SPEEDRUN" in payload["text"]
    assert "CONFIRMED" in payload["blocks"][0]["text"]["text"] or "SPEEDRUN" in payload["blocks"][0]["text"]["text"]

def test_slack_notifier_dry_run():
    notifier = SlackNotifier()
    now = datetime.datetime.now(datetime.timezone.utc)
    item = LaunchItem(
        id="dry_run_01",
        company_name="DryRun Labs",
        source=LaunchSource.YC_DIRECTORY,
        detected_at=now
    )
    success, ts = notifier.send_launch_alert(item, dry_run=True)
    assert success is True
    assert "mock_ts" in ts
