import logging
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserSession, get_current_user, get_db
from app.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)
from app.repositories.rbac_repository import RbacRepository
from app.schemas.auth import (
    ForgotRequest,
    ForgotResponse,
    Login2FARequiredResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    ResetRequest,
)
from app.services.auth_service import AuthService
from app.services.role_resolver import RoleResolver

router = APIRouter(prefix="/api/auth", tags=["auth"])

_rate_limiter = RateLimiter()
logger.warning(
    "RateLimiter usando diccionario en memoria. "
    "En producción con múltiples réplicas, reemplazar con Redis. "
    "El estado se pierde en cada restart."
)


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth_user import AuthUser
    from app.models.usuario import Usuario

    auth_user = await db.get(AuthUser, current_user.user_id)
    if not auth_user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    usuario = await db.get(Usuario, current_user.user_id)
    effective = await RbacRepository.get_effective_permissions(db, current_user.roles)

    return MeResponse(
        id=str(current_user.user_id),
        email=auth_user.email,
        tenant_id=str(current_user.tenant_id),
        nombre=usuario.nombre if usuario else "",
        apellidos=usuario.apellidos if usuario else "",
        roles=current_user.roles,
        permissions=effective,
    )


async def _get_auth_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    tenant_id = getattr(request.state, "tenant_id", None) or uuid.UUID(int=0)
    auth_repo = AuthRepository(db, tenant_id)
    refresh_repo = RefreshTokenRepository(db, tenant_id)
    reset_repo = ResetTokenRepository(db, tenant_id)
    role_resolver = RoleResolver(db, tenant_id)
    return AuthService(
        session=db,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=_rate_limiter,
        role_resolver=role_resolver,
    )


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(_get_auth_service),
):
    ip = request.client.host if request.client else "unknown"
    result = await auth_service.login(body.email, body.password, ip)
    if result.get("requires_2fa"):
        return Login2FARequiredResponse(
            requires_2fa=True,
            session_token=result["session_token"],
        )
    return LoginResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer",
    )


@router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    result = await auth_service.refresh(body.refresh_token)
    return RefreshResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    await auth_service.logout(body.refresh_token)
    return {"message": "Logged out successfully"}


@router.post("/forgot")
async def forgot(
    body: ForgotRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    result = await auth_service.forgot_password(body.email)
    return ForgotResponse(message=result["message"])


@router.post("/reset")
async def reset(
    body: ResetRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    result = await auth_service.reset_password(body.token, body.new_password)
    return {"message": result["message"]}
