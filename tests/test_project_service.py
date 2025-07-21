import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.project_service import ProjectService
from models import Project, User


class TestProjectService:
    @pytest.mark.asyncio
    async def test_add_member_to_project(self):
        fake_project = Project(name="Test Project")
        fake_project.id = 1
        fake_project.members = []

        fake_user = User(username="tester", discord_id=123)
        fake_user.id = 2

        session_mock = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = fake_project
        session_mock.execute.return_value = result_mock
        session_mock.commit = AsyncMock()

        with patch("services.project_service.get_async_session") as session_cm, \
             patch("services.project_service.UserService.get_or_create_user", new=AsyncMock(return_value=fake_user)):
            session_cm.return_value.__aenter__.return_value = session_mock
            session_cm.return_value.__aexit__.return_value = None

            result = await ProjectService.add_member_to_project(1, 123)

            assert result is True
            assert fake_user in fake_project.members
            session_mock.commit.assert_awaited_once()

