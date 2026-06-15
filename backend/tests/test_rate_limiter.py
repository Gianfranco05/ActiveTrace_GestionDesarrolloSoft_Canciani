from unittest.mock import patch

from app.core.rate_limiter import RateLimiter


def test_allow_within_limit():
    limiter = RateLimiter(max_attempts=5, window_seconds=60)
    for _ in range(5):
        assert limiter.is_allowed("192.168.1.1", "user@test.com") is True


def test_block_exceeds_limit():
    limiter = RateLimiter(max_attempts=5, window_seconds=60)
    for _ in range(5):
        limiter.is_allowed("192.168.1.1", "user@test.com")
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is False


def test_different_ip_same_email_independent():
    limiter = RateLimiter(max_attempts=2, window_seconds=60)
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is True
    assert limiter.is_allowed("192.168.1.2", "user@test.com") is True
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is True


def test_same_ip_different_email_independent():
    limiter = RateLimiter(max_attempts=2, window_seconds=60)
    assert limiter.is_allowed("192.168.1.1", "a@test.com") is True
    assert limiter.is_allowed("192.168.1.1", "b@test.com") is True
    assert limiter.is_allowed("192.168.1.1", "a@test.com") is True


def test_reset_on_success():
    limiter = RateLimiter(max_attempts=2, window_seconds=60)
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is True
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is True
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is False
    limiter.reset("192.168.1.1", "user@test.com")
    assert limiter.is_allowed("192.168.1.1", "user@test.com") is True


def test_expired_entries_cleaned():
    limiter = RateLimiter(max_attempts=2, window_seconds=0.2)
    base_time = 1_000_000.0
    with patch("app.core.rate_limiter.time.time", return_value=base_time):
        assert limiter.is_allowed("192.168.1.1", "user@test.com") is True
        assert limiter.is_allowed("192.168.1.1", "user@test.com") is True
        assert limiter.is_allowed("192.168.1.1", "user@test.com") is False
    with patch("app.core.rate_limiter.time.time", return_value=base_time + 0.25):
        assert limiter.is_allowed("192.168.1.1", "user@test.com") is True
