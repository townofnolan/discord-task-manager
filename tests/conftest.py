"""Test configuration and fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import AsyncSessionLocal


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create test database session."""
    # TODO: Set up test database
    # For now, return a mock
    mock_session = AsyncMock(spec=AsyncSession)
    yield mock_session


@pytest.fixture
def mock_discord_user():
    """Mock Discord user for testing."""
    class MockUser:
        def __init__(self, id=12345, username="testuser"):
            self.id = id
            self.username = username
            self.display_name = "Test User"
    
    return MockUser()


@pytest.fixture
def mock_discord_interaction():
    """Mock Discord interaction for testing."""
    class MockInteraction:
        def __init__(self, user=None, channel_id=67890):
            self.user = user or MockUser()
            self.channel_id = channel_id
            self.guild_id = 11111
        
        async def response(self):
            return AsyncMock()
    
    return MockInteraction()