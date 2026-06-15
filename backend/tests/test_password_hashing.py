
from app.core.security import hash_password, verify_password


def test_hash_and_verify():
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_wrong_password_fails_verify():
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert verify_password("WrongPass456!", hashed) is False


def test_same_password_different_hashes():
    password = "SecurePass123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2
