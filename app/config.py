from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"

    agent_max_iterations: int = 40
    agent_workspace: Path = Path("/app/workspace")
    agent_skills_dir: Path = Path("/app/skills")
    agent_allow_shell: bool = True
    agent_shell_timeout: int = 600

    redis_url: str = "redis://redis:6379/0"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
