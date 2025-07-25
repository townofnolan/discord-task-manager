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
    async def get_time_entries_for_user(
        user_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[TimeEntry]:
        """Fetch time entries for a specific user with optional pagination."""
        async with get_async_session() as session:
            query = (
                select(TimeEntry)
                .options(selectinload(TimeEntry.task))
                .where(TimeEntry.user_id == user_id)
            )
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            result = await session.execute(query)
            return result.scalars()

    @staticmethod
    async def get_time_entries_for_task(
        task_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[TimeEntry]:
        """Fetch time entries for a specific task with optional pagination."""
        async with get_async_session() as session:
            query = (
                select(TimeEntry)
                .options(selectinload(TimeEntry.user))
                .where(TimeEntry.task_id == task_id)
            )
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            result = await session.execute(query)
            return result.scalars()
