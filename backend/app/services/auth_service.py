import hashlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limiter import RateLimiter
from app.core.security import (
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
)
from app.models.auth_user import AuthUser, RefreshToken, ResetToken
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)
from app.services.role_resolver import RoleResolver

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        auth_repo: AuthRepository,
        refresh_repo: RefreshTokenRepository,
        reset_repo: ResetTokenRepository,
        rate_limiter: RateLimiter,
        role_resolver: RoleResolver | None = None,
    ):
        self._session = session
        self._auth_repo = auth_repo
        self._refresh_repo = refresh_repo
        self._reset_repo = reset_repo
        self._rate_limiter = rate_limiter
        self._role_resolver = role_resolver

    async def login(
        self, email: str, password: str, ip: str,
    ) -> dict:
        if not self._rate_limiter.is_allowed(ip, email):
            raise HTTPException(status_code=429, detail="Too many requests")

        user = await self._auth_repo.find_by_email_across_tenants(email)
        if user is None or not user.is_active:
            self._rate_limiter.reset(ip, email)
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        self._rate_limiter.reset(ip, email)

        if user.is_2fa_enabled:
            session_token = await self._create_temp_2fa_token(str(user.id), str(user.tenant_id))
            return {"requires_2fa": True, "session_token": session_token}

        tokens = await self._issue_tokens(user)
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
        }

    async def refresh(self, raw_token: str) -> dict:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        stored = await self._refresh_repo.find_by_hash(token_hash)
        if stored is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if stored.is_used:
            await self._refresh_repo.invalidate_all_for_user(stored.user_id)
            logger.warning(
                "Compromise detected: reused refresh token for user %s", stored.user_id,
            )
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        expires = stored.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        stored.is_used = True
        await self._session.commit()

        user = await self._auth_repo.get(stored.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        tokens = await self._issue_tokens(user)
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
        }

    async def logout(self, raw_token: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        stored = await self._refresh_repo.find_by_hash(token_hash)
        if stored is None or stored.is_used:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        stored.is_used = True
        await self._session.commit()

    async def forgot_password(self, email: str) -> dict:
        user = await self._auth_repo.find_by_email_across_tenants(email)
        if user is not None:
            raw_token = secrets.token_urlsafe(48)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            reset_token = ResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
            self._session.add(reset_token)
            await self._session.commit()
            logger.info("Reset link for %s: /auth/reset?token=%s", email, raw_token)

        return {"message": "If the email exists, a reset link has been sent"}

    async def reset_password(self, token: str, new_password: str) -> dict:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stored = await self._reset_repo.find_by_hash(token_hash)
        if stored is None or stored.is_used:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        expires = stored.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        stored.is_used = True

        user = await self._auth_repo.get(stored.user_id)
        if user is None:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user.password_hash = hash_password(new_password)

        await self._refresh_repo.invalidate_all_for_user(user.id)
        await self._session.commit()

        return {"message": "Password has been reset successfully"}

    async def verify_2fa_login(self, session_token: str, totp_code: str) -> dict:
        try:
            payload = verify_access_token(session_token)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired session") from exc

        if payload.get("type") != "2fa_pending":
            raise HTTPException(status_code=401, detail="Invalid session token")

        user_id = uuid.UUID(payload["sub"])
        user = await self._auth_repo.get(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        from app.services.twofa_service import TwoFAService
        twofa = TwoFAService(self._session, user_id)
        valid = twofa.verify_code(totp_code, user.otp_secret)
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid TOTP code")

        tokens = await self._issue_tokens(user)
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
        }

    async def _resolve_roles(self, user: AuthUser) -> list[str]:
        if self._role_resolver is None:
            return []
        try:
            return await self._role_resolver.resolve_roles(user.id)
        except Exception:
            logger.exception("Failed to resolve roles for user %s", user.id)
            return []

    async def _issue_tokens(self, user: AuthUser) -> dict:
        roles = await self._resolve_roles(user)
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            roles=roles,
        )

        raw_refresh = secrets.token_hex(64)
        refresh_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
        refresh_token = RefreshToken(
            token_hash=refresh_hash,
            user_id=user.id,
            tenant_id=user.tenant_id,
            expires_at=datetime.now(UTC) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
            ),
        )
        self._session.add(refresh_token)
        await self._session.commit()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
        }

    async def _create_temp_2fa_token(self, user_id: str, tenant_id: str) -> str:
        """Create a temporary 2FA pending token with resolved roles."""
        from datetime import timedelta as _td

        from app.core.security import create_access_token as _cat

        roles: list[str] = []
        if self._role_resolver is not None:
            try:
                roles = await self._role_resolver.resolve_roles(uuid.UUID(user_id))
            except Exception:
                logger.exception("Failed to resolve roles for 2fa token, user %s", user_id)

        return _cat(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            expires_delta=_td(minutes=5),
            token_type="2fa_pending",
        )
