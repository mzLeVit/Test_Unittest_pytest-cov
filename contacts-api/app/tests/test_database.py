import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AsyncSessionLocal

@pytest.mark.asyncio
@patch('app.database.AsyncSessionLocal')
async def test_get_db(mock_AsyncSessionLocal):
    # Мокування
    mock_session = AsyncMock(AsyncSession)
    mock_AsyncSessionLocal.return_value.__aenter__.return_value = mock_session

    async for db in get_db():
        # Перевірка, що функція повертає сесію
        assert db == mock_session
        # Перевірка, що контекст менеджер правильно використовує сесію
        mock_AsyncSessionLocal.assert_called_once()

    # Перевірка, що контекст менеджер правильно виконує aenter та aexit
    mock_AsyncSessionLocal.return_value.__aenter__.assert_called_once()
    mock_AsyncSessionLocal.return_value.__aexit__.assert_called_once()
