## ADDED Requirements

### Requirement: AES-256-GCM encrypt function

The system SHALL provide an `encrypt(plaintext: str) -> str` function that uses AES-256-GCM symmetric encryption. The encryption key SHALL be derived from the `ENCRYPTION_KEY` configuration variable. The output SHALL be a single base64-encoded string containing the nonce, ciphertext, and authentication tag.

#### Scenario: Encrypt produces deterministic-length output

- **WHEN** a plaintext string is encrypted with `encrypt()`
- **THEN** the output SHALL be a non-empty base64-encoded string

#### Scenario: Encrypt uses random nonce

- **WHEN** the same plaintext is encrypted twice
- **THEN** the two ciphertext outputs SHALL be different (different nonce each time)

### Requirement: AES-256-GCM decrypt function

The system SHALL provide a `decrypt(ciphertext_b64: str) -> str` function that reverses `encrypt()`. It SHALL return the original plaintext given a valid ciphertext and the correct encryption key.

#### Scenario: Decrypt recovers original plaintext

- **WHEN** a ciphertext produced by `encrypt()` is passed to `decrypt()`
- **THEN** the output SHALL exactly match the original plaintext

#### Scenario: Decrypt raises on invalid ciphertext

- **WHEN** an invalid or tampered ciphertext is passed to `decrypt()`
- **THEN** the function SHALL raise `EncryptionError`

### Requirement: Null-safe helpers

The system SHALL provide `encrypt_or_none(value: str | None) -> str | None` and `decrypt_or_none(value: str | None) -> str | None` that return `None` for `None` input without attempting encryption/decryption.

#### Scenario: Encrypt_or_none returns None for None input

- **WHEN** `encrypt_or_none(None)` is called
- **THEN** it SHALL return `None`

#### Scenario: Decrypt_or_none returns None for None input

- **WHEN** `decrypt_or_none(None)` is called
- **THEN** it SHALL return `None`

### Requirement: Secrets never logged

The `encrypt()` and `decrypt()` functions SHALL NOT log the plaintext, ciphertext, or encryption key under any circumstance.

#### Scenario: Encrypt does not log plaintext

- **WHEN** `encrypt()` is called with a sensitive value
- **THEN** the plaintext SHALL NOT appear in any log output

### Requirement: EncryptionError exception

The system SHALL define an `EncryptionError` exception class (in `core/exceptions.py`) that is raised when encryption or decryption operations fail.

#### Scenario: EncryptionError raised on wrong key

- **WHEN** `decrypt()` is called with a ciphertext encrypted with a different key
- **THEN** it SHALL raise `EncryptionError`
