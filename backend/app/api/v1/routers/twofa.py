import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserSession, get_current_user, get_db
from app.core.rate_limiter import RateLimiter
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)
from app.schemas.auth import (
    Disable2FARequest,
    Enroll2FAResponse,
    Verify2FARequest,
    VerifyLogin2FARequest,
)
from app.services.auth_service import AuthService
from app.services.twofa_service import TwoFAService

router = APIRouter(prefix="/api/auth/2fa", tags=["2fa"])


async def _get_auth_service(db: AsyncSession) -> AuthService:
    dummy_tenant = uuid.UUID(int=0)
    auth_repo = AuthRepository(db, dummy_tenant)
    refresh_repo = RefreshTokenRepository(db, dummy_tenant)
    reset_repo = ResetTokenRepository(db, dummy_tenant)
    return AuthService(
        session=db,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=RateLimiter(),
    )


@router.post("/enroll")
async def enroll_2fa(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    twofa = TwoFAService(db, current_user.user_id)
    result = await twofa.enroll()
    return Enroll2FAResponse(
        secret_base32=result["secret_base32"],
        qr_uri=result["qr_uri"],
    )


@router.post("/verify")
async def verify_2fa(
    body: Verify2FARequest,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    twofa = TwoFAService(db, current_user.user_id)
    result = await twofa.verify(body.totp_code)
    return {"enabled": result["enabled"]}


@router.post("/verify-login")
async def verify_login_2fa(
    body: VerifyLogin2FARequest,
    db: AsyncSession = Depends(get_db),
):
    auth_service = await _get_auth_service(db)
    result = await auth_service.verify_2fa_login(
        body.session_token, body.totp_code,
    )
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
    }


@router.post("/disable")
async def disable_2fa(
    body: Disable2FARequest,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    twofa = TwoFAService(db, current_user.user_id)
    result = await twofa.disable(body.password)
    return {"enabled": result["enabled"]}
