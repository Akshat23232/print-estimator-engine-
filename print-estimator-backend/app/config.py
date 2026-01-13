"""
Application Configuration

Centralized configuration using pydantic-settings.
All environment variables are validated at startup.

Design Decision:
- Use pydantic-settings for type-safe configuration
- Fail fast on missing required config (better than runtime errors)
- Sensible defaults for optional settings
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Required:
        OPENAI_API_KEY: API key for LLM service
        
    Optional:
        OPENAI_BASE_URL: Custom endpoint for OpenAI-compatible APIs
        N8N_WEBHOOK_URL: Webhook for n8n workflow integration
        LOG_LEVEL: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
    """
    
    # LLM Configuration
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"  # Cost-effective default
    
    # n8n Integration
    # NOTE: If not set, webhook calls are skipped (useful for local dev)
    n8n_webhook_url: str | None = None
    
    # Application Settings
    log_level: str = "INFO"
    
    # Pricing config path (relative to app directory)
    pricing_config_path: str = "data/pricing.json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    
    Using lru_cache ensures we only parse environment once.
    This is the recommended pattern from FastAPI docs.
    """
    return Settings()
