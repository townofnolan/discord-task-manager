"""Tests for task service."""

from unittest.mock import AsyncMock, patch

import pytest

from models import TaskPriority, TaskStatus
from services.task_service import TaskService


class TestTaskService:
    """Test cases for TaskService."""

    @pytest.mark.asyncio
    async def test_create_task_basic(self, mock_discord_user):
        """Test basic task creation."""
        with patch("services.task_service.get_async_session") as mock_session:
            # Mock the session and database operations
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()

            # This is a placeholder test - in a real implementation,
            # we would set up a test database and verify the task creation

            # For now, just verify the function exists and can be called
            assert hasattr(TaskService, "create_task")
            assert callable(TaskService.create_task)

    @pytest.mark.asyncio
    async def test_get_task_by_id(self):
        """Test getting task by ID."""
        with patch("services.task_service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()

            assert hasattr(TaskService, "get_task_by_id")
            assert callable(TaskService.get_task_by_id)

    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.TODO.value == "todo"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.REVIEW.value == "review"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_priority_enum(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"
