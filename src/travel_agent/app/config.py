"""Application configuration and settings for the Travel Agent backend."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime configuration for the API and downstream services."""

    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key used by the LangChain-powered agent",
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Default chat completion model used for the agent",
    )
    GROQ_API_KEY: str = Field(
        default="",
        description="Groq API key used for high-quality intent extraction.",
    )
    GROQ_MODEL: str = Field(
        default="groq/compound-mini",
        description="Groq model to use for intent extraction.",
    )
    GOOGLE_MAPS_API_KEY: str = Field(
        default="",
        description="Google Maps API key for Places and Distance Matrix APIs.",
    )
    TAVILY_API_KEY: str = Field(
        default="",
        description="Tavily API key for web search results.",
    )
    DEBUG_LANGUAGE: bool = Field(
        default=False,
        description="Toggle to include language detection details in responses",
    )

    MCP_SERVER_URL: Optional[str] = Field(
        default=None,
        description="Optional external MCP server endpoint."
        " When omitted, built-in tools are used.",
    )

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()


settings = get_settings()
