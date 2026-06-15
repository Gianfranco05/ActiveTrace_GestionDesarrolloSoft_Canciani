import uuid

import pyotp
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    decrypt_or_none,
    encrypt_or_none,
    verify_password,
)
from app.models.auth_user import AuthUser


class TwoFAService:
    def __init__(self, session: AsyncSession, user_id: uuid.UUID):
        self._session = session
        self._user_id = user_id
        self._temp_secret: str | None = None

    async def enroll(self) -> dict:
        secret = pyotp.random_base32()
        self._temp_secret = secret
        user = await self._session.get(AuthUser, self._user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        qr_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=settings.TOTP_ISSUER_NAME,
        )

        return {
            "secret_base32": secret,
            "qr_uri": qr_uri,
        }

    async def verify(self, totp_code: str) -> dict:
        if self._temp_secret is None:
            raise HTTPException(status_code=400, detail="Enroll first")

        if not pyotp.TOTP(self._temp_secret).verify(totp_code):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")

        user = await self._session.get(AuthUser, self._user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        user.otp_secret = encrypt_or_none(self._temp_secret)
        user.is_2fa_enabled = True
        await self._session.commit()

        return {"enabled": True}

    def verify_code(self, totp_code: str, encrypted_secret: str | None) -> bool:
        if encrypted_secret is None:
            return False
        secret = decrypt_or_none(encrypted_secret)
        if secret is None:
            return False
        return pyotp.TOTP(secret).verify(totp_code)

    async def disable(self, password: str) -> dict:
        user = await self._session.get(AuthUser, self._user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")

        user.otp_secret = None
        user.is_2fa_enabled = False
        await self._session.commit()

        return {"enabled": False}
