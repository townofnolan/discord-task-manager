"""Task service for managing tasks."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Project, Task, TaskPriority, TaskStatus, User
from services.user_service import UserService
from utils import get_async_session

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks."""

    @staticmethod
    async def create_task(
        title: str,
        creator_discord_id: int,
        description: Optional[str] = None,
        project_id: Optional[int] = None,
        priority: str = TaskPriority.MEDIUM.value,
        assignee_discord_ids: Optional[List[int]] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        estimated_hours: Optional[float] = None,
        discord_channel_id: Optional[int] = None,
        discord_message_id: Optional[int] = None,
    ) -> Task:
        """Create a new task."""
        try:
            logger.info(f"Creating task: {title}, creator: {creator_discord_id}")

            async with get_async_session() as session:
                try:
                    # Get or create creator
                    try:
                        creator = await UserService.get_or_create_user(
                            discord_id=creator_discord_id,
                            username="Unknown",  # Will be updated when we have more info
                        )
                        logger.info(f"Creator user fetched/created: {creator.id}")
                    except Exception as e:
                        logger.error(
                            f"Failed to get/create creator: {e}", exc_info=True
                        )
                        raise

                    # Create task
                    try:
                        task = Task(
                            title=title,
                            description=description,
                            creator_id=creator.id,
                            project_id=project_id,
                            priority=priority,
                            due_date=due_date,
                            tags=tags or [],
                            custom_fields=custom_fields or {},
                            estimated_hours=estimated_hours,
                            discord_channel_id=discord_channel_id,
                            discord_message_id=discord_message_id,
                            is_recurring=False,  # Ensure recurring field is set
                        )
                        logger.info(f"Task object created: {title}")
                    except Exception as e:
                        logger.error(
                            f"Failed to create task object: {e}", exc_info=True
                        )
                        raise

                    # Add task to session and flush
                    try:
                        session.add(task)
                        logger.info("Task added to session")
                        await session.flush()  # Get task ID
                        logger.info(f"Session flushed, task ID: {task.id}")
                    except Exception as e:
                        logger.error(f"Failed to flush session: {e}", exc_info=True)
                        raise

                    # Add assignees if provided
                    try:
                        if assignee_discord_ids:
                            for discord_id in assignee_discord_ids:
                                assignee = await UserService.get_or_create_user(
                                    discord_id=discord_id, username="Unknown"
                                )
                                task.assignees.append(assignee)
                            logger.info(f"Added assignees: {assignee_discord_ids}")
                    except Exception as e:
                        logger.error(f"Failed to add assignees: {e}", exc_info=True)
                        raise

                    # Commit and refresh
                    try:
                        await session.commit()
                        logger.info("Session committed")
                        await session.refresh(task)
                        logger.info(f"Task refreshed: {task.id}")
                        return task
                    except Exception as e:
                        logger.error(f"Failed to commit or refresh: {e}", exc_info=True)
                        raise

                except Exception:
                    await session.rollback()
                    raise

        except Exception as e:
            logger.error(f"Task creation failed: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_task_by_id(task_id: int) -> Optional[Task]:
        """Get task by ID with all related data."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                    selectinload(Task.time_entries),
                )
                .where(Task.id == task_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_task_by_discord_message(message_id: int) -> Optional[Task]:
        """Get task by Discord message ID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                )
                .where(Task.discord_message_id == message_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_task(task_id: int, **kwargs) -> Optional[Task]:
        """Update task with provided fields."""
        async with get_async_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            # Handle status change to completed
            if kwargs.get("status") == TaskStatus.DONE.value and not task.completed_at:
                task.completed_at = datetime.now(timezone.utc)
            elif kwargs.get("status") != TaskStatus.DONE.value:
                task.completed_at = None

            await session.commit()
            await session.refresh(task)
            return task

    @staticmethod
    async def assign_users_to_task(task_id: int, user_discord_ids: List[int]) -> bool:
        """Assign users to a task."""
        async with get_async_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                return False

            # Clear existing assignees
            task.assignees.clear()

            # Add new assignees
            for discord_id in user_discord_ids:
                user = await UserService.get_or_create_user(
                    discord_id=discord_id, username="Unknown"
                )
                task.assignees.append(user)

            await session.commit()
            return True

    @staticmethod
    async def delete_task(task_id: int) -> bool:
        """Delete a task."""
        async with get_async_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                await session.delete(task)
                await session.commit()
                return True
            return False

    @staticmethod
    async def get_tasks_for_user(
        user_discord_id: int,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Task]:
        """Get tasks assigned to a user."""
        async with get_async_session() as session:
            # Get user
            user = await UserService.get_user_by_discord_id(user_discord_id)
            if not user:
                return []

            query = (
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                )
                .join(Task.assignees)
                .where(User.id == user.id)
            )

            if status:
                query = query.where(Task.status == status)

            if project_id:
                query = query.where(Task.project_id == project_id)

            query = query.order_by(desc(Task.created_at)).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_tasks_for_project(
        project_id: int, status: Optional[str] = None, limit: int = 100
    ) -> List[Task]:
        """Get tasks for a project."""
        async with get_async_session() as session:
            query = (
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                )
                .where(Task.project_id == project_id)
            )

            if status:
                query = query.where(Task.status == status)

            query = query.order_by(desc(Task.created_at)).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def search_tasks(
        query: str,
        user_discord_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Task]:
        """Search tasks by title and description."""
        async with get_async_session() as session:
            sql_query = (
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                )
                .where(
                    or_(
                        Task.title.ilike(f"%{query}%"),
                        Task.description.ilike(f"%{query}%"),
                    )
                )
            )

            if user_discord_id:
                user = await UserService.get_user_by_discord_id(user_discord_id)
                if user:
                    sql_query = sql_query.join(Task.assignees).where(User.id == user.id)

            if project_id:
                sql_query = sql_query.where(Task.project_id == project_id)

            if status:
                sql_query = sql_query.where(Task.status == status)

            sql_query = sql_query.order_by(desc(Task.created_at)).limit(limit)

            result = await session.execute(sql_query)
            return result.scalars().all()

    @staticmethod
    async def get_overdue_tasks() -> List[Task]:
        """Get all overdue tasks."""
        async with get_async_session() as session:
            # Get tasks with due dates in the past and not completed or cancelled
            now = datetime.now(timezone.utc)
            result = await session.execute(
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                )
                .where(
                    and_(
                        Task.due_date < now,
                        Task.status != TaskStatus.DONE.value,
                        Task.status != TaskStatus.CANCELLED.value,
                    )
                )
                .order_by(asc(Task.due_date))
            )
            return result.scalars().all()

    @staticmethod
    async def create_recurring_task(
        title: str,
        creator_discord_id: int,
        recurrence_pattern: str,
        recurrence_frequency: int = 1,
        description: Optional[str] = None,
        project_id: Optional[int] = None,
        priority: str = TaskPriority.MEDIUM.value,
        assignee_discord_ids: Optional[List[int]] = None,
        due_date: Optional[datetime] = None,
        recurrence_end_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        estimated_hours: Optional[float] = None,
        discord_channel_id: Optional[int] = None,
        discord_message_id: Optional[int] = None,
    ) -> Task:
        """Create a new recurring task."""
        async with get_async_session() as session:
            # Get or create creator
            creator = await UserService.get_or_create_user(
                discord_id=creator_discord_id, username="Unknown"
            )

            # Create task
            task = Task(
                title=title,
                description=description,
                creator_id=creator.id,
                project_id=project_id,
                priority=priority,
                due_date=due_date,
                tags=tags or [],
                custom_fields=custom_fields or {},
                estimated_hours=estimated_hours,
                discord_channel_id=discord_channel_id,
                discord_message_id=discord_message_id,
                is_recurring=True,
                recurrence_pattern=recurrence_pattern,
                recurrence_frequency=recurrence_frequency,
                recurrence_end_date=recurrence_end_date,
                last_recurrence_date=datetime.now(timezone.utc),
            )

            session.add(task)
            await session.flush()  # Get task ID

            # Add assignees if provided
            if assignee_discord_ids:
                for discord_id in assignee_discord_ids:
                    assignee = await UserService.get_or_create_user(
                        discord_id=discord_id, username="Unknown"
                    )
                    task.assignees.append(assignee)

            await session.commit()
            await session.refresh(task)
            return task

    @staticmethod
    async def update_recurring_task_settings(
        task_id: int,
        is_recurring: Optional[bool] = None,
        recurrence_pattern: Optional[str] = None,
        recurrence_frequency: Optional[int] = None,
        recurrence_end_date: Optional[datetime] = None,
    ) -> Optional[Task]:
        """Update recurring task settings."""
        async with get_async_session() as session:
            task = await session.get(Task, task_id)
            if not task:
                return None

            if is_recurring is not None:
                task.is_recurring = is_recurring

            if recurrence_pattern is not None:
                task.recurrence_pattern = recurrence_pattern

            if recurrence_frequency is not None:
                task.recurrence_frequency = recurrence_frequency

            if recurrence_end_date is not None:
                task.recurrence_end_date = recurrence_end_date

            await session.commit()
            await session.refresh(task)
            return task

    @staticmethod
    async def get_tasks_by_date_range(
        start_date: datetime, end_date: datetime, include_no_due_date: bool = False
    ) -> List[Task]:
        """Get tasks with due dates in the specified range."""
        async with get_async_session() as session:
            # Base query
            query = select(Task).options(
                selectinload(Task.creator),
                selectinload(Task.assignees),
                selectinload(Task.project),
            )

            # Add date range filter
            date_filter = and_(Task.due_date >= start_date, Task.due_date < end_date)

            # Optionally include tasks with no due date
            if include_no_due_date:
                date_filter = or_(date_filter, Task.due_date.is_(None))

            # Only include active tasks
            status_filter = and_(
                Task.status != TaskStatus.DONE.value,
                Task.status != TaskStatus.CANCELLED.value,
            )

            # Add filters to query
            query = query.where(and_(date_filter, status_filter))

            # Execute query
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def process_recurring_tasks() -> List[Task]:
        """Process all recurring tasks and create new instances if needed."""
        now = datetime.now(timezone.utc)
        new_tasks = []

        async with get_async_session() as session:
            # Get all active recurring tasks
            result = await session.execute(
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project),
                )
                .where(
                    and_(
                        Task.is_recurring.is_(True),
                        or_(
                            Task.recurrence_end_date.is_(None),
                            Task.recurrence_end_date >= now,
                        ),
                        Task.status != TaskStatus.CANCELLED.value,
                    )
                )
            )
            recurring_tasks = result.scalars().all()

            for task in recurring_tasks:
                # Check if it's time to create a new task instance
                if not task.last_recurrence_date:
                    continue

                # Calculate next occurrence based on pattern
                next_date = None

                if task.recurrence_pattern == "daily":
                    next_date = task.last_recurrence_date + timedelta(
                        days=task.recurrence_frequency
                    )
                elif task.recurrence_pattern == "weekly":
                    next_date = task.last_recurrence_date + timedelta(
                        weeks=task.recurrence_frequency
                    )
                elif task.recurrence_pattern == "monthly":
                    # Add months (approximate)
                    next_month = (
                        task.last_recurrence_date.month + task.recurrence_frequency
                    )
                    next_year = task.last_recurrence_date.year + (next_month - 1) // 12
                    next_month = ((next_month - 1) % 12) + 1
                    next_date = task.last_recurrence_date.replace(
                        year=next_year, month=next_month
                    )

                # If it's time to create a new task instance
                if next_date and next_date <= now:
                    # Create new task with same properties
                    # Calculate new due date based on recurrence pattern if original had a due date
                    new_due_date = None
                    if task.due_date:
                        if task.recurrence_pattern == "daily":
                            new_due_date = task.due_date + timedelta(
                                days=task.recurrence_frequency
                            )
                        elif task.recurrence_pattern == "weekly":
                            new_due_date = task.due_date + timedelta(
                                weeks=task.recurrence_frequency
                            )
                        elif task.recurrence_pattern == "monthly":
                            # Add months (approximate)
                            next_month = task.due_date.month + task.recurrence_frequency
                            next_year = task.due_date.year + (next_month - 1) // 12
                            next_month = ((next_month - 1) % 12) + 1
                            new_due_date = task.due_date.replace(
                                year=next_year, month=next_month
                            )

                    # Create new task instance
                    new_task = Task(
                        title=task.title,
                        description=task.description,
                        creator_id=task.creator_id,
                        project_id=task.project_id,
                        priority=task.priority,
                        due_date=new_due_date,
                        tags=task.tags,
                        custom_fields=task.custom_fields,
                        estimated_hours=task.estimated_hours,
                        discord_channel_id=task.discord_channel_id,
                    )

                    session.add(new_task)
                    await session.flush()

                    # Add same assignees
                    for assignee in task.assignees:
                        new_task.assignees.append(assignee)

                    # Update last recurrence date on the original task
                    task.last_recurrence_date = now

                    new_tasks.append(new_task)

            if new_tasks:
                await session.commit()
                # Refresh all new tasks to get complete data
                for new_task in new_tasks:
                    await session.refresh(new_task)

            return new_tasks
