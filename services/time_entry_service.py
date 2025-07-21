"""Service for managing time tracking entries."""

import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import TimeEntry
from utils import get_async_session

logger = logging.getLogger(__name__)


class TimeEntryService:
    """Service for managing time entries."""

    @staticmethod
    async def create_time_entry(
        task_id: int,
        user_id: int,
        duration_hours: float,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> TimeEntry:
        """Create and persist a time entry."""
        async with get_async_session() as session:
            entry = TimeEntry(
                task_id=task_id,
                user_id=user_id,
                duration_hours=duration_hours,
                description=description,
                start_time=start_time,
                end_time=end_time,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

    @staticmethod
    async def get_time_entries_for_user(user_id: int) -> List[TimeEntry]:
        """Fetch all time entries for a specific user."""
        async with get_async_session() as session:
            result = await session.execute(
                select(TimeEntry)
                .options(selectinload(TimeEntry.task))
                .where(TimeEntry.user_id == user_id)
            )
            return result.scalars().all()

    @staticmethod
    async def get_time_entries_for_task(task_id: int) -> List[TimeEntry]:
        """Fetch all time entries for a specific task."""
        async with get_async_session() as session:
            result = await session.execute(
                select(TimeEntry)
                .options(selectinload(TimeEntry.user))
                .where(TimeEntry.task_id == task_id)
            )
            return result.scalars().all()
