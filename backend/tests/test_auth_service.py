import hashlib
import secrets
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import RateLimiter
from app.core.security import hash_password
from app.models.auth_user import AuthUser, ResetToken
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)
from app.services.auth_service import AuthService
from app.services.twofa_service import TwoFAService


@pytest.fixture
def auth_service(db_session: AsyncSession, tenant) -> AuthService:
    auth_repo = AuthRepository(db_session, tenant.id)
    refresh_repo = RefreshTokenRepository(db_session, tenant.id)
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    rate_limiter = RateLimiter(max_attempts=10, window_seconds=60)
    return AuthService(
        session=db_session,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=rate_limiter,
    )


def _create_test_user(db_session, tenant, email="login_test@test.com", password="Secure123"):
    user = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(password),
    )
    db_session.add(user)
    return user


# --- Login Tests ---

@pytest.mark.asyncio
async def test_login_success(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant)
    await db_session.commit()

    result = await auth_service.login("login_test@test.com", "Secure123", "127.0.0.1")
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(auth_service, db_session, tenant):
    _create_test_user(db_session, tenant)
    await db_session.commit()

    with pytest.raises(Exception) as exc:
        await auth_service.login("login_test@test.com", "WrongPass1", "127.0.0.1")
    assert "Invalid" in str(exc.value)


@pytest.mark.asyncio
async def test_login_nonexistent_email(auth_service):
    with pytest.raises(Exception) as exc:
        await auth_service.login("nobody@test.com", "SomePass1", "127.0.0.1")
    assert "Invalid" in str(exc.value)


@pytest.mark.asyncio
async def test_login_inactive_user(auth_service, db_session, tenant):
    user = AuthUser(
        tenant_id=tenant.id,
        email="inactive@test.com",
        password_hash=hash_password("Secure123"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(Exception) as exc:
        await auth_service.login("inactive@test.com", "Secure123", "127.0.0.1")
    assert "Invalid" in str(exc.value)


# --- Refresh Tests ---

@pytest.mark.asyncio
async def test_refresh_success(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant)
    await db_session.commit()

    login_result = await auth_service.login("login_test@test.com", "Secure123", "127.0.0.1")
    old_refresh = login_result["refresh_token"]

    result = await auth_service.refresh(old_refresh)
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["refresh_token"] != old_refresh


@pytest.mark.asyncio
async def test_refresh_used_token(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant)
    await db_session.commit()

    login_result = await auth_service.login("login_test@test.com", "Secure123", "127.0.0.1")
    old_refresh = login_result["refresh_token"]

    await auth_service.refresh(old_refresh)

    with pytest.raises(Exception) as exc:
        await auth_service.refresh(old_refresh)
    assert "Invalid" in str(exc.value)


@pytest.mark.asyncio
async def test_refresh_nonexistent(auth_service):
    with pytest.raises(Exception) as exc:
        await auth_service.refresh("nonexistent_token")
    assert "Invalid" in str(exc.value)


# --- Logout Tests ---

@pytest.mark.asyncio
async def test_logout_success(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant)
    await db_session.commit()

    login_result = await auth_service.login("login_test@test.com", "Secure123", "127.0.0.1")
    refresh_token = login_result["refresh_token"]

    await auth_service.logout(refresh_token)

    with pytest.raises(Exception) as exc:
        await auth_service.refresh(refresh_token)
    assert "Invalid" in str(exc.value)


# --- Forgot Password Tests ---

@pytest.mark.asyncio
async def test_forgot_password_creates_token(auth_service, db_session, tenant):
    _create_test_user(db_session, tenant, email="forgot_test@test.com")
    await db_session.commit()

    result = await auth_service.forgot_password("forgot_test@test.com")
    assert result["message"] is not None


@pytest.mark.asyncio
async def test_forgot_nonexistent_email_returns_200(auth_service):
    result = await auth_service.forgot_password("nobody@test.com")
    assert result["message"] is not None


# --- Reset Password Tests ---

@pytest.mark.asyncio
async def test_reset_password_updates_hash(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="reset_me@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    from app.repositories.auth_repository import ResetTokenRepository
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset_token = ResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(reset_token)
    await db_session.commit()

    old_hash = user.password_hash
    result = await auth_service.reset_password(raw_token, "NewSecure123")
    assert result["message"] is not None

    await db_session.refresh(user)
    assert user.password_hash != old_hash


@pytest.mark.asyncio
async def test_reset_expired_token(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="reset_expired@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset_token = ResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db_session.add(reset_token)
    await db_session.commit()

    with pytest.raises(Exception) as exc:
        await auth_service.reset_password(raw_token, "NewSecure123")
    assert "expired" in str(exc.value).lower()


# --- 2FA Service Tests ---

@pytest.mark.asyncio
async def test_2fa_enroll_generates_secret(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="2fa_enroll@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    twofa = TwoFAService(db_session, user.id)
    result = await twofa.enroll()
    assert "secret_base32" in result
    assert "qr_uri" in result
    assert result["qr_uri"].startswith("otpauth://")


@pytest.mark.asyncio
async def test_2fa_verify_valid_totp(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="2fa_verify@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    twofa = TwoFAService(db_session, user.id)
    enroll_result = await twofa.enroll()

    import pyotp
    totp = pyotp.TOTP(enroll_result["secret_base32"])
    valid_code = totp.now()

    result = await twofa.verify(valid_code)
    assert result["enabled"] is True

    await db_session.refresh(user)
    assert user.is_2fa_enabled is True
    assert user.otp_secret is not None


@pytest.mark.asyncio
async def test_2fa_verify_invalid_totp(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="2fa_badcode@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    twofa = TwoFAService(db_session, user.id)
    await twofa.enroll()

    with pytest.raises(Exception) as exc:
        await twofa.verify("000000")
    assert "Invalid" in str(exc.value)


# --- Login with 2FA ---

@pytest.mark.asyncio
async def test_login_requires_2fa(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="2fa_login@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    twofa = TwoFAService(db_session, user.id)
    enroll = await twofa.enroll()
    import pyotp
    totp = pyotp.TOTP(enroll["secret_base32"])
    await twofa.verify(totp.now())

    result = await auth_service.login("2fa_login@test.com", "Secure123", "127.0.0.1")
    assert result.get("requires_2fa") is True
    assert "session_token" in result
    assert "access_token" not in result


@pytest.mark.asyncio
async def test_verify_login_totp_gate(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="2fa_gate@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    twofa = TwoFAService(db_session, user.id)
    enroll = await twofa.enroll()
    import pyotp
    totp = pyotp.TOTP(enroll["secret_base32"])
    await twofa.verify(totp.now())

    login_result = await auth_service.login("2fa_gate@test.com", "Secure123", "127.0.0.1")
    session_token = login_result["session_token"]

    valid_code = totp.now()
    result = await auth_service.verify_2fa_login(session_token, valid_code)
    assert "access_token" in result
    assert "refresh_token" in result


@pytest.mark.asyncio
async def test_disable_2fa_with_password(auth_service, db_session, tenant):
    user = _create_test_user(db_session, tenant, email="2fa_disable@test.com")
    await db_session.commit()
    await db_session.refresh(user)

    twofa = TwoFAService(db_session, user.id)
    enroll = await twofa.enroll()
    import pyotp
    totp = pyotp.TOTP(enroll["secret_base32"])
    await twofa.verify(totp.now())

    result = await twofa.disable("Secure123")
    assert result["enabled"] is False

    await db_session.refresh(user)
    assert user.is_2fa_enabled is False
    assert user.otp_secret is None
