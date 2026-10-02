"""Application settings, loaded from environment variables.

Nothing here has a secret default. JEV_API_KEY is optional on purpose: its
absence is what puts the app into replay mode (see app/jev/client.py).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = API_ROOT.parent.parent
SEED_DIR = API_ROOT / "data" / "seed"
DEFAULT_FIXTURES_DIR = REPO_ROOT / "eval" / "fixtures"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Jev access (see docs/PHASE1_PLAN.md section 2.2 for the verified route)
    jev_base_url: str = "https://ai-gateway.vercel.sh/typesafe"
    jev_api_key: str | None = None
    jev_model: str = "typesafe-ai/jev"

    # auto: live if jev_api_key is set and the daily budget is not exhausted; replay otherwise.
    # live: force live mode (fails loudly if no key).
    # replay: force replay mode even if a key is present (useful for CI and demos).
    jev_mode: str = "auto"

    daily_budget_tokens: int = 200_000
    rate_limit_per_min: int = 20

    cors_origins: str = "http://localhost:3000"

    audit_db_path: str = str(API_ROOT / "data" / "audit.db")
    fixtures_dir: str = str(DEFAULT_FIXTURES_DIR)

    app_version: str = "0.1.0"
    policy_version: str = "phase1-v1"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
