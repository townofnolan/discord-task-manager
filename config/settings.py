"""Configuration management for Discord Task Manager."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Discord Configuration
    discord_bot_token: str = Field(..., description="Discord bot token")
    discord_guild_id: Optional[int] = Field(None, description="Discord guild ID")
    bot_prefix: str = Field("!", description="Bot command prefix")
    
    # Database Configuration
    database_url: str = Field(..., description="Database connection URL")
    database_name: str = Field("discord_task_manager", description="Database name")
    
    # Application Configuration
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    default_timezone: str = Field("UTC", description="Default timezone")
    
    # Feature Flags
    enable_nlp: bool = Field(True, description="Enable NLP features")
    enable_calendar: bool = Field(True, description="Enable calendar integration")
    enable_time_tracking: bool = Field(True, description="Enable time tracking")
    
    # Railway Configuration
    railway_static_url: Optional[str] = Field(None, description="Railway static URL")
    railway_project_id: Optional[str] = Field(None, description="Railway project ID")
    railway_environment: Optional[str] = Field(None, description="Railway environment")


# Global settings instance
settings = Settings()