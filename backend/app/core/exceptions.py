class EncryptionError(Exception):
    """Raised when encryption or decryption operations fail."""


class TenantNotFoundError(Exception):
    """Raised when tenant resolution fails."""
