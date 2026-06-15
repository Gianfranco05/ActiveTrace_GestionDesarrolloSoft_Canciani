import pytest

from app.core.exceptions import EncryptionError
from app.core.security import decrypt, decrypt_or_none, encrypt, encrypt_or_none


def test_encrypt_decrypt_roundtrip():
    plaintext = "sensitive-data-123"
    ciphertext = encrypt(plaintext)
    decrypted = decrypt(ciphertext)
    assert decrypted == plaintext


def test_encrypt_different_nonce():
    plaintext = "same-data"
    c1 = encrypt(plaintext)
    c2 = encrypt(plaintext)
    assert c1 != c2


def test_decrypt_invalid_ciphertext_raises():
    with pytest.raises(EncryptionError):
        decrypt("not-a-valid-ciphertext")


def test_decrypt_tampered_ciphertext_raises():
    ciphertext = encrypt("important")
    tampered = ciphertext[:-1] + ("X" if ciphertext[-1] != "X" else "Y")
    with pytest.raises(EncryptionError):
        decrypt(tampered)


def test_encrypt_or_none():
    assert encrypt_or_none(None) is None
    result = encrypt_or_none("hello")
    assert result is not None
    assert isinstance(result, str)


def test_decrypt_or_none():
    assert decrypt_or_none(None) is None
    result = decrypt_or_none(encrypt("hello"))
    assert result == "hello"


def test_encrypt_logs_nothing(caplog):
    caplog.set_level("DEBUG")
    encrypt("secret-plaintext")
    assert "secret-plaintext" not in caplog.text
    assert "ENCRYPTION_KEY" not in caplog.text
