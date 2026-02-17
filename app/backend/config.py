"""Configuration management for the Alinta Energy Assistant backend."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Databricks configuration
    databricks_host: str = os.getenv("DATABRICKS_HOST", "")
    databricks_token: str = os.getenv("DATABRICKS_TOKEN", "")

    # Vector Search configuration
    vector_search_endpoint: str = "alinta_support_endpoint"
    vector_search_index: str = "main.alinta.content_vector_index"

    # LLM configuration
    llm_model: str = "databricks-gpt-oss-120b-preview"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7

    # Retrieval configuration
    top_k_results: int = 3
    similarity_threshold: float = 0.5

    # Application configuration
    app_name: str = "Alinta Energy Assistant"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS configuration
    cors_origins: list = ["*"]

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def validate_config() -> bool:
    """
    Validate that required configuration is present.

    Returns:
        True if configuration is valid

    Raises:
        ValueError if required configuration is missing
    """
    if not settings.databricks_host:
        raise ValueError("DATABRICKS_HOST environment variable is required")

    if not settings.databricks_token:
        raise ValueError("DATABRICKS_TOKEN environment variable is required")

    return True
