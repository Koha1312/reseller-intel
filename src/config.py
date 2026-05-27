"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen3:4b"
    ollama_api_key: str = "ollama"

    ebay_app_id: str = ""
    ebay_dev_id: str = ""
    ebay_cert_id: str = ""
    ebay_environment: str = "SANDBOX"

    database_url: str = "sqlite:///data/reseller.db"

    log_level: str = "INFO"


settings = Settings()
