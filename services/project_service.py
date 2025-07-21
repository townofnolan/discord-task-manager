"""Project service for managing projects."""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Project, User
from services.user_service import UserService
from utils import get_async_session

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects."""

    @staticmethod
    async def create_project(
        name: str,
        description: Optional[str] = None,
        discord_channel_id: Optional[int] = None,
        color: str = "#3498db",
    ) -> Project:
        """Create a new project."""
        async with get_async_session() as session:
            project = Project(
                name=name,
                description=description,
                discord_channel_id=discord_channel_id,
                color=color,
            )

            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project

    @staticmethod
    async def get_project_by_id(project_id: int) -> Optional[Project]:
        """Get project by ID with all related data."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Project)
                .options(selectinload(Project.members), selectinload(Project.tasks))
                .where(Project.id == project_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_project_by_channel(channel_id: int) -> Optional[Project]:
        """Get project by Discord channel ID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Project)
                .options(selectinload(Project.members), selectinload(Project.tasks))
                .where(Project.discord_channel_id == channel_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_all_projects(include_inactive: bool = False) -> List[Project]:
        """Get all projects."""
        async with get_async_session() as session:
            query = select(Project).options(
                selectinload(Project.members), selectinload(Project.tasks)
            )

            if not include_inactive:
                query = query.where(Project.is_active.is_(True))

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update_project(project_id: int, **kwargs) -> Optional[Project]:
        """Update project with provided fields."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)

            await session.commit()
            await session.refresh(project)
            return project

    @staticmethod
    async def add_member_to_project(project_id: int, user_discord_id: int) -> bool:
        """Add a member to a project."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Project)
                .options(selectinload(Project.members))
                .where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return False

            user = await UserService.get_or_create_user(
                discord_id=user_discord_id, username="Unknown"
            )

            if user not in project.members:
                project.members.append(user)
                await session.commit()

            return True

    @staticmethod
    async def remove_member_from_project(project_id: int, user_discord_id: int) -> bool:
        """Remove a member from a project."""
        async with get_async_session() as session:
            project = await ProjectService.get_project_by_id(project_id)
            if not project:
                return False

            user = await UserService.get_user_by_discord_id(user_discord_id)
            if not user:
                return False

            if user in project.members:
                project.members.remove(user)
                await session.commit()

            return True

    @staticmethod
    async def get_projects_for_user(user_discord_id: int) -> List[Project]:
        """Get all projects a user is a member of."""
        async with get_async_session() as session:
            user = await UserService.get_user_by_discord_id(user_discord_id)
            if not user:
                return []

            result = await session.execute(
                select(Project)
                .options(selectinload(Project.members), selectinload(Project.tasks))
                .join(Project.members)
                .where(User.id == user.id)
                .where(Project.is_active.is_(True))
            )
            return result.scalars().all()

    @staticmethod
    async def delete_project(project_id: int) -> bool:
        """Delete a project (sets inactive instead of actual deletion)."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if project:
                project.is_active = False
                await session.commit()
                return True
            return False

    @staticmethod
    async def search_projects(query: str) -> List[Project]:
        """Search projects by name or description."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Project)
                .options(selectinload(Project.members), selectinload(Project.tasks))
                .where(
                    (Project.name.ilike(f"%{query}%"))
                    | (Project.description.ilike(f"%{query}%"))
                )
                .where(Project.is_active.is_(True))
            )
            return result.scalars().all()
