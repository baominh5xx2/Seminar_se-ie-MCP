"""
Core Configuration Module
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server Configuration
    SERVER_NAME: str = Field(default="AI Assistant MCP Server", description="MCP server name")
    SERVER_VERSION: str = Field(default="1.0.0", description="Server version")
    
    # Backend API Configuration
    BACKEND_API_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API base URL"
    )
    BACKEND_API_TIMEOUT: int = Field(default=30, description="API timeout in seconds")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    
    # Weather API Configuration
    WEATHER_API_KEY: str = Field(
        default=YOUR_WEATHER_API_KEY,
        description="OpenWeatherMap API key (get free key at https://openweathermap.org/api)"
    )
    
    # Google Drive Configuration (for document resources)
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = Field(
        default=None,
        description="Google Drive folder ID for documents"
    )
    GOOGLE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None,
        description="Path to Google credentials JSON"
    )
    
    # Agent Configuration
    MAX_ITERATIONS: int = Field(default=10, description="Max agent iterations")
    TIMEOUT: int = Field(default=300, description="Agent timeout in seconds")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Global settings instance
settings = Settings()
