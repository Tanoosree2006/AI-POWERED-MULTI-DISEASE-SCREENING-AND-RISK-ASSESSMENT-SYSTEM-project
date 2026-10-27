"""Application settings, read from environment variables or a .env file."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_SECRET = "dev-only-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI-Powered Multi-Disease Screening API"
    environment: str = "development"
    database_url: str = "sqlite:///./screening.db"
    secret_key: str = DEV_SECRET
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    ml_src_dir: Path = REPO_ROOT / "ml" / "src"
    ml_eval_dir: Path = REPO_ROOT / "ml" / "evaluation"
    rate_limit_per_minute: int = 60

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_for_environment(self):
        if self.environment == "production" and self.secret_key == DEV_SECRET:
            raise RuntimeError("SECRET_KEY must be set in production")


settings = Settings()
