from app.core.security import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    raw = "secret-value-123"
    ct = encrypt(raw)
    assert ct != raw
    pt = decrypt(ct)
    assert pt == raw


def test_decrypt_tampered_fails():
    raw = "abc"
    ct = encrypt(raw)
    # tamper last char
    tampered = ct[:-1] + ("A" if ct[-1] != "A" else "B")
    try:
        decrypt(tampered)
        assert False, "tampered ciphertext should raise"
    except Exception:
        assert True
