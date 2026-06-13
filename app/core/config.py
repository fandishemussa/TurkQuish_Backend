from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TurkQuish Backend"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    artifact_dir: Path = Path("app/artifacts")
    database_url: str = "sqlite:///./turkquish.db"
    cors_origins: str = "*"
    url_hash_salt: str = "change-me-in-production"
    enable_url_transformer: bool = True
    histgb_confidence_threshold: float = 0.89
    histgb_margin_threshold: float = 0.20
    url_transformer_override_confidence_threshold: float = 0.95
    url_transformer_override_margin_threshold: float = 0.50
    risk_boundary_low: float = 0.35
    risk_boundary_high: float = 0.60
    max_url_length: int = 4096
    request_timeout_seconds: float = 10.0
    rate_limit_requests_per_minute: int = 100000
    enable_rate_limiting: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()



