import pytest
from unittest.mock import patch, mock_open
from pydantic_settings import BaseSettings
import os

# Налаштування для тестів
class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"

@pytest.fixture
def mock_env_file():
    """Фікстура для заміни .env файлу під час тестування"""
    with patch("builtins.open", mock_open(read_data="DATABASE_URL=sqlite:///test.db")):
        yield

@pytest.mark.parametrize("env_content,expected_url", [
    ("DATABASE_URL=sqlite:///test.db", "sqlite:///test.db"),
    ("DATABASE_URL=postgresql://user:password@localhost/dbname", "postgresql://user:password@localhost/dbname"),
])
def test_settings_loads_correctly(mock_env_file, env_content, expected_url):
    """Тестування правильного завантаження налаштувань з .env файлу"""
    with patch("builtins.open", mock_open(read_data=env_content)):
        settings = Settings()
        assert settings.database_url == expected_url

@pytest.mark.parametrize("env_content", [
    "",
    "OTHER_SETTING=value",
])
def test_settings_missing_database_url(mock_env_file, env_content):
    """Тестування ситуації, коли DATABASE_URL не задано в .env файлі"""
    with patch("builtins.open", mock_open(read_data=env_content)):
        with pytest.raises(ValueError, match="Field 'database_url' must be defined"):
            Settings()
