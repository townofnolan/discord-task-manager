import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from services.time_entry_service import TimeEntryService
from models import TimeEntry


class TestTimeEntryService:
    @pytest.mark.asyncio
    async def test_create_time_entry(self):
        session_mock = AsyncMock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        session_mock.add = MagicMock()

        with patch("services.time_entry_service.get_async_session") as session_cm:
            session_cm.return_value.__aenter__.return_value = session_mock
            session_cm.return_value.__aexit__.return_value = None

            start = datetime.now(timezone.utc)
            end = start

            entry = await TimeEntryService.create_time_entry(
                task_id=1,
                user_id=2,
                duration_hours=1.5,
                description="work",
                start_time=start,
                end_time=end,
            )

            session_mock.add.assert_called_once()
            session_mock.commit.assert_awaited_once()
            session_mock.refresh.assert_awaited_once_with(entry)

