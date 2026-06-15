import pytest

from app.core.security import decrypt, encrypt


@pytest.mark.asyncio
async def test_encrypt_pii_fields_round_trip():
    pii_values = {
        "dni": "12345678",
        "cuil": "20-12345678-9",
        "cbu": "1234567890123456789012",
        "email": "user@example.com",
        "phone": "+54 11 5555-1234",
        "empty": "",
        "long": "a" * 1000,
        "unicode": "ñandú café 日本語",
    }

    for field, value in pii_values.items():
        encrypted = encrypt(value)
        assert encrypted != value
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

        decrypted = decrypt(encrypted)
        assert decrypted == value, f"Mismatch for {field}: {decrypted} != {value}"
