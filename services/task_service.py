"""Task service for managing tasks."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from models import Task, TaskStatus, TaskPriority, User, Project
from utils import get_async_session
from services.user_service import UserService

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
        discord_message_id: Optional[int] = None
    ) -> Task:
        """Create a new task."""
        async with get_async_session() as session:
            # Get or create creator
            creator = await UserService.get_or_create_user(
                discord_id=creator_discord_id,
                username="Unknown"  # Will be updated when we have more info
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
                discord_message_id=discord_message_id
            )
            
            session.add(task)
            await session.flush()  # Get task ID
            
            # Add assignees if provided
            if assignee_discord_ids:
                for discord_id in assignee_discord_ids:
                    assignee = await UserService.get_or_create_user(
                        discord_id=discord_id,
                        username="Unknown"
                    )
                    task.assignees.append(assignee)
            
            await session.commit()
            await session.refresh(task)
            return task
    
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
                    selectinload(Task.time_entries)
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
                    selectinload(Task.project)
                )
                .where(Task.discord_message_id == message_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def update_task(
        task_id: int,
        **kwargs
    ) -> Optional[Task]:
        """Update task with provided fields."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # Handle status change to completed
            if kwargs.get('status') == TaskStatus.DONE.value and not task.completed_at:
                task.completed_at = datetime.now(timezone.utc)
            elif kwargs.get('status') != TaskStatus.DONE.value:
                task.completed_at = None
            
            await session.commit()
            await session.refresh(task)
            return task
    
    @staticmethod
    async def assign_users_to_task(task_id: int, user_discord_ids: List[int]) -> bool:
        """Assign users to a task."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return False
            
            # Clear existing assignees
            task.assignees.clear()
            
            # Add new assignees
            for discord_id in user_discord_ids:
                user = await UserService.get_or_create_user(
                    discord_id=discord_id,
                    username="Unknown"
                )
                task.assignees.append(user)
            
            await session.commit()
            return True
    
    @staticmethod
    async def delete_task(task_id: int) -> bool:
        """Delete a task."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
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
        limit: int = 50
    ) -> List[Task]:
        """Get tasks assigned to a user."""
        async with get_async_session() as session:
            # Get user
            user = await UserService.get_user_by_discord_id(user_discord_id)
            if not user:
                return []
            
            query = select(Task).options(
                selectinload(Task.creator),
                selectinload(Task.assignees),
                selectinload(Task.project)
            ).join(Task.assignees).where(User.id == user.id)
            
            if status:
                query = query.where(Task.status == status)
            
            if project_id:
                query = query.where(Task.project_id == project_id)
            
            query = query.order_by(desc(Task.created_at)).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @staticmethod
    async def get_tasks_for_project(
        project_id: int,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks for a project."""
        async with get_async_session() as session:
            query = select(Task).options(
                selectinload(Task.creator),
                selectinload(Task.assignees),
                selectinload(Task.project)
            ).where(Task.project_id == project_id)
            
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
        limit: int = 50
    ) -> List[Task]:
        """Search tasks by title and description."""
        async with get_async_session() as session:
            sql_query = select(Task).options(
                selectinload(Task.creator),
                selectinload(Task.assignees),
                selectinload(Task.project)
            ).where(
                or_(
                    Task.title.ilike(f"%{query}%"),
                    Task.description.ilike(f"%{query}%")
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
            now = datetime.now(timezone.utc)
            result = await session.execute(
                select(Task)
                .options(
                    selectinload(Task.creator),
                    selectinload(Task.assignees),
                    selectinload(Task.project)
                )
                .where(
                    and_(
                        Task.due_date < now,
                        Task.status != TaskStatus.DONE.value,
                        Task.status != TaskStatus.CANCELLED.value
                    )
                )
                .order_by(asc(Task.due_date))
            )
            return result.scalars().all()