"""
State Manager Tests
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.services.state_manager import StateManager


class TestStateManager:
    @pytest.fixture
    def manager(self):
        return StateManager()

    @pytest.mark.asyncio
    async def test_new_session(self, manager):
        with patch("src.services.redis_client.get_session", return_value=None):
            with patch("src.services.redis_client.save_session", new_callable=AsyncMock):
                session = await manager.get_session("client-1", "user-1", "web")
                assert session["client_id"] == "client-1"
                assert session["user_id"] == "user-1"
                assert session["channel"] == "web"
                assert session["slots"] == {}

    @pytest.mark.asyncio
    async def test_update_slots(self, manager):
        with patch("src.services.redis_client.get_session", return_value={
            "client_id": "client-1",
            "user_id": "user-1",
            "channel": "web",
            "slots": {"order_id": "1122"},
            "intent_history": [],
            "turn_count": 0,
        }):
            with patch("src.services.redis_client.save_session", new_callable=AsyncMock) as mock_save:
                session = await manager.update_slots(
                    "client-1", "user-1", "web",
                    {"tracking_number": "1Z999"}
                )
                assert session["slots"]["order_id"] == "1122"
                assert session["slots"]["tracking_number"] == "1Z999"
                mock_save.assert_called_once()
