from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    DATABASE_URL: str
    SECRET_KEY: str = Field(min_length=32)
    ENCRYPTION_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)
    JWT_ALGORITHM: str = Field(default="HS256")
    TOTP_ISSUER_NAME: str = Field(default="activia-trace")
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    OTEL_SERVICE_NAME: str = "activia-trace"
    OTEL_TRACES_EXPORTER: str = "none"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters (got {len(v)})"
            )
        return v

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key_length(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError(
                f"ENCRYPTION_KEY must be exactly 32 characters (got {len(v)})"
            )
        return v


settings = Settings()
