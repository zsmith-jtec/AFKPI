"""Application configuration settings."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    # App info
    app_name: str = "FOS"
    app_version: str = "0.1.0"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/fos.db"

    # JWT Auth
    secret_key: str = "change-this-in-production-use-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # Data paths
    data_dir: Path = Path("./data")
    sample_data_dir: Path = Path("./data/sample")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
