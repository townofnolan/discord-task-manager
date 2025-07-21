"""User service for managing Discord users."""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import User
from utils import get_async_session

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users."""

    @staticmethod
    async def get_or_create_user(
        discord_id: int,
        username: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        """Get existing user or create new one."""
        async with get_async_session() as session:
            # Try to find existing user
            result = await session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Update user info if changed
                user.username = username
                if display_name:
                    user.display_name = display_name
                if avatar_url:
                    user.avatar_url = avatar_url
            else:
                # Create new user
                user = User(
                    discord_id=discord_id,
                    username=username,
                    display_name=display_name,
                    avatar_url=avatar_url,
                )
                session.add(user)

            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_user_by_discord_id(discord_id: int) -> Optional[User]:
        """Get user by Discord ID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        async with get_async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    @staticmethod
    async def search_users(query: str) -> List[User]:
        """Search users by username or display name."""
        async with get_async_session() as session:
            result = await session.execute(
                select(User)
                .where(
                    (User.username.ilike(f"%{query}%"))
                    | (User.display_name.ilike(f"%{query}%"))
                )
                .where(User.is_active == True)
            )
            return result.scalars().all()

    @staticmethod
    async def get_all_users() -> List[User]:
        """Get all active users."""
        async with get_async_session() as session:
            result = await session.execute(select(User).where(User.is_active == True))
            return result.scalars().all()

    @staticmethod
    async def update_user_timezone(user_id: int, timezone: str) -> bool:
        """Update user's timezone."""
        async with get_async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                user.timezone = timezone
                await session.commit()
                return True
            return False

    @staticmethod
    async def deactivate_user(user_id: int) -> bool:
        """Deactivate a user."""
        async with get_async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                user.is_active = False
                await session.commit()
                return True
            return False
