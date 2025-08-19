"""
Configuration management for the Library MCP Server.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, validator


class ServerConfig(BaseModel):
    """Server configuration model."""
    
    # File paths
    books_file: Path = Field(
        default=Path("books.json"),
        description="Path to the books JSON file"
    )
    
    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Feature flags
    enable_search: bool = Field(default=True, description="Enable book search functionality")
    enable_stats: bool = Field(default=True, description="Enable library statistics")
    max_books: int = Field(default=10000, description="Maximum number of books", ge=1)
    
    # Performance settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds", ge=0)
    
    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v
    
    @validator('books_file')
    def validate_books_file(cls, v: Path) -> Path:
        """Validate books file path."""
        # Create parent directory if it doesn't exist
        v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        return cls(
            books_file=Path(os.getenv("LIBRARY_BOOKS_FILE", "books.json")),
            host=os.getenv("LIBRARY_HOST", "127.0.0.1"),
            port=int(os.getenv("LIBRARY_PORT", "8000")),
            log_level=os.getenv("LIBRARY_LOG_LEVEL", "INFO"),
            enable_search=os.getenv("LIBRARY_ENABLE_SEARCH", "true").lower() == "true",
            enable_stats=os.getenv("LIBRARY_ENABLE_STATS", "true").lower() == "true",
            max_books=int(os.getenv("LIBRARY_MAX_BOOKS", "10000")),
            cache_enabled=os.getenv("LIBRARY_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("LIBRARY_CACHE_TTL", "300")),
        )
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        validate_assignment = True


# Global configuration instance
config = ServerConfig.from_env()


def get_config() -> ServerConfig:
    """Get the current configuration."""
    return config


def update_config(**kwargs) -> ServerConfig:
    """Update the configuration with new values."""
    global config
    current_dict = config.dict()
    current_dict.update(kwargs)
    config = ServerConfig(**current_dict)
    return config