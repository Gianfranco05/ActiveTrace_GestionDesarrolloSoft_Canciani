import pytest
from pydantic import ValidationError


class TestSettingsValidation:
    def test_valid_settings_from_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        settings = Settings()
        assert settings.DATABASE_URL == "postgresql+asyncpg://u:p@localhost:5432/db"
        assert settings.SECRET_KEY == "a" * 32
        assert settings.ENCRYPTION_KEY == "b" * 32
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_default_access_token_expire(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

        from app.core.config import Settings

        settings = Settings()
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_missing_database_url_fails(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        # _env_file=None prevents reading DATABASE_URL from the .env fallback
        with pytest.raises(ValidationError):
            Settings(_env_file=None)  # type: ignore[call-arg]

    def test_short_secret_key_fails(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "too-short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings()

    def test_invalid_encryption_key_length_fails(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "too-short")

        from app.core.config import Settings

        with pytest.raises(ValidationError, match="ENCRYPTION_KEY"):
            Settings()
