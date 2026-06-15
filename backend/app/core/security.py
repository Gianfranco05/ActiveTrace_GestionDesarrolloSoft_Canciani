"""Security utilities for activia-trace.

# C-02: AES-256-GCM encryption — implemented
# C-03: JWT, Argon2id, password hashing — implemented
"""

import base64
import os
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher as _Argon2PasswordHasher
from argon2.exceptions import VerifyMismatchError as _VerifyMismatchError
from jose import jwt as _jwt

from app.core.config import Settings
from app.core.exceptions import EncryptionError

_KEY: bytes | None = None
_settings = Settings()


def _get_key() -> bytes:
    global _KEY
    if _KEY is not None:
        return _KEY
    key = _settings.ENCRYPTION_KEY.encode("utf-8")
    if len(key) != 32:
        raise EncryptionError(
            f"ENCRYPTION_KEY must be exactly 32 bytes (got {len(key)})",
        )
    _KEY = key
    return _KEY


def encrypt(plaintext: str) -> str:
    """Encrypt a string with AES-256-GCM.

    Returns base64-encoded string containing nonce + ciphertext + tag.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _get_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt(ciphertext_b64: str) -> str:
    """Decrypt a base64-encoded AES-256-GCM ciphertext.

    Returns the original plaintext string.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _get_key()
    try:
        payload = base64.urlsafe_b64decode(ciphertext_b64)
    except Exception as exc:
        raise EncryptionError("invalid ciphertext encoding") from exc

    if len(payload) < 13:
        raise EncryptionError("ciphertext too short")
    nonce = payload[:12]
    ciphertext = payload[12:]
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise EncryptionError("decryption failed") from exc
    return plaintext.decode("utf-8")


def encrypt_or_none(value: str | None) -> str | None:
    """Encrypt a value or return None if input is None."""
    if value is None:
        return None
    return encrypt(value)


def decrypt_or_none(value: str | None) -> str | None:
    """Decrypt a value or return None if input is None.

    If decryption fails (e.g. the value is plaintext from a bootstrap or
    migration), the raw value is returned as-is so the application does not
    crash with a 500.
    """
    if value is None:
        return None
    try:
        return decrypt(value)
    except EncryptionError:
        return value


_ph = _Argon2PasswordHasher()



def _get_jwt_secret() -> str:
    return _settings.SECRET_KEY  # type: ignore[return-value]


def _get_jwt_algorithm() -> str:
    return _settings.JWT_ALGORITHM


def _get_access_token_expire() -> int:
    return _settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(
    user_id: str,
    tenant_id: str,
    roles: list[str],
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=_get_access_token_expire())
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return _jwt.encode(payload, _get_jwt_secret(), algorithm=_get_jwt_algorithm())


def verify_access_token(token: str) -> dict:
    return _jwt.decode(
        token,
        _get_jwt_secret(),
        algorithms=[_get_jwt_algorithm()],
    )


def hash_password(plaintext: str) -> str:
    """Hash a password using Argon2id.

    # C-03: Argon2id password hashing — implemented
    """
    return _ph.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a password against an Argon2id hash.

    # C-03: Argon2id password hashing — implemented
    """
    try:
        return _ph.verify(hashed, plaintext)
    except _VerifyMismatchError:
        return False
