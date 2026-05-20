"""
Zenny Core Configuration
Pydantic-Settings validates all env vars at startup.
No .env file in repo — set vars on Railway/Hetzner/Supabase dashboards.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Server ──
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # ── Supabase ──
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")

    # ── Redis ──
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_username: Optional[str] = Field(default=None, alias="REDIS_USERNAME")

    # ── LLM Providers ──
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    deepseek_api_key: str = Field(alias="DEEPSEEK_API_KEY")

    # ── Voiceflow ──
    voiceflow_dmapi_key: str = Field(alias="VOICEFLOW_DMAPI_KEY")

    # ── n8n ──
    n8n_webhook_url: str = Field(alias="N8N_WEBHOOK_URL")
    n8n_secret: str = Field(alias="N8N_SECRET")

    # ── Integrations ──
    sendgrid_api_key: Optional[str] = Field(default=None, alias="SENDGRID_API_KEY")
    twilio_auth_token: Optional[str] = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    meta_app_secret: Optional[str] = Field(default=None, alias="META_APP_SECRET")

    # ── Security ──
    admin_password: str = Field(alias="ADMIN_PASSWORD")
    jwt_secret: str = Field(alias="JWT_SECRET")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def redis_url(self) -> str:
        auth = ""
        if self.redis_username and self.redis_password:
            auth = f"{self.redis_username}:{self.redis_password}@"
        elif self.redis_password:
            auth = f":{self.redis_password}@"
        return f"redis://{auth}{self.redis_host}:{self.redis_port}"


# Singleton — import this everywhere
settings = Settings()
