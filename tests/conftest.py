import pytest
from yc_launch_monitor.config import settings

@pytest.fixture(autouse=True)
def setup_test_settings():
    settings.POND_ACCESS_KEY = "test_pond_access_key_2026"
    settings.TELEGRAM_BOT_TOKEN = "7740806969:AAG_zC8L6a3-b8t4BroNtnvMXN_MVW1BCl0"
    settings.TELEGRAM_CHAT_ID = "7899086191"
    yield
