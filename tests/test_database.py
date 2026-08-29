import pytest
import os
import tempfile
import datetime
from yc_launch_monitor.models import LaunchItem, LaunchStatus, LaunchSource, ProgramType, FounderInfo
from yc_launch_monitor.database import DatabaseManager

@pytest.fixture
def temp_db():
    # Use SQLite in-memory database for clean, isolated test runs
    db = DatabaseManager(db_path=":memory:")
    return db

def test_save_and_retrieve_launch(temp_db):
    now = datetime.datetime.now(datetime.timezone.utc)
    item = LaunchItem(
        id="test_01",
        company_name="Acme AI",
        slug="acme-ai",
        website="https://acme.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[FounderInfo(name="Jane Doe", handle="@janedoe", title="CEO")],
        description="Autonomous AI infrastructure.",
        post_text="We got into YC S26!",
        post_url="https://x.com/janedoe/status/123",
        detected_at=now
    )

    is_new, is_upgraded = temp_db.save_launch(item)
    assert is_new is True
    assert is_upgraded is False

    retrieved = temp_db.get_by_id("test_01")
    assert retrieved is not None
    assert retrieved.company_name == "Acme AI"
    assert retrieved.status == LaunchStatus.EARLY_SIGNAL
    assert len(retrieved.founders) == 1
    assert retrieved.founders[0].name == "Jane Doe"

def test_deduplication_and_upgrade_to_confirmed(temp_db):
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Early signal on X
    early_item = LaunchItem(
        id="test_early",
        company_name="Acme AI",
        slug="acme-ai",
        website="https://acme.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[FounderInfo(name="Jane Doe", handle="@janedoe")],
        detected_at=now
    )
    is_new, is_upgraded = temp_db.save_launch(early_item)
    assert is_new is True
    assert is_upgraded is False

    # 2. Re-detecting same early signal should be deduplicated
    is_new2, is_upgraded2 = temp_db.save_launch(early_item)
    assert is_new2 is False
    assert is_upgraded2 is False

    # 3. Subsequently detected on official YC Directory -> upgraded to CONFIRMED
    confirmed_item = LaunchItem(
        id="yc_dir_12345",
        company_name="Acme AI",
        slug="acme-ai",
        website="https://acme.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.YC_DIRECTORY,
        status=LaunchStatus.CONFIRMED,
        description="Official YC company description",
        detected_at=now + datetime.timedelta(days=1)
    )
    is_new3, is_upgraded3 = temp_db.save_launch(confirmed_item)
    assert is_new3 is False
    assert is_upgraded3 is True

    # Verify status in database
    existing = temp_db.find_existing_company("Acme AI")
    assert existing is not None
    assert existing.status == LaunchStatus.CONFIRMED
    assert existing.confirmed_at is not None

def test_stats_and_filtering(temp_db):
    item1 = LaunchItem(
        id="t1",
        company_name="Alpha",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL
    )
    item2 = LaunchItem(
        id="t2",
        company_name="Beta",
        batch="SR006",
        program_type=ProgramType.SPEEDRUN,
        source=LaunchSource.SPEEDRUN_DIRECTORY,
        status=LaunchStatus.CONFIRMED
    )
    temp_db.save_launch(item1)
    temp_db.save_launch(item2)

    stats = temp_db.get_stats()
    assert stats.total_tracked_companies == 2
    assert stats.early_signal_count == 1
    assert stats.confirmed_count == 1
    assert stats.speedrun_count == 1
    assert stats.yc_count == 1

    early_list = temp_db.list_launches(status=LaunchStatus.EARLY_SIGNAL)
    assert len(early_list) == 1
    assert early_list[0].company_name == "Alpha"

def test_idempotency_store(temp_db):
    temp_db.save_idempotent_response(
        run_id="run_100",
        action_id="check_new_launches",
        parameters={"send_slack": True},
        response_data={"status": "completed", "output": []}
    )

    cached = temp_db.get_idempotent_response("run_100")
    assert cached is not None
    assert cached["status"] == "completed"

    missing = temp_db.get_idempotent_response("run_non_existent")
    assert missing is None
