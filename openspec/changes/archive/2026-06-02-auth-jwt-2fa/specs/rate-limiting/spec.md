## ADDED Requirements

### Requirement: Rate limiter — 5 attempts per 60 seconds
The system SHALL implement an in-memory rate limiter that allows a maximum of 5 login attempts per 60 seconds per IP+email combination. The window SHALL be sliding (based on timestamps, not fixed intervals).

#### Scenario: Allow requests within limit
- **WHEN** a client makes 5 or fewer login attempts within a 60-second window for the same IP+email
- **THEN** the rate limiter returns is_allowed = True

#### Scenario: Block requests exceeding limit
- **WHEN** a client makes 6 login attempts within a 60-second window for the same IP+email
- **THEN** the rate limiter returns is_allowed = False

#### Scenario: Window slides forward
- **WHEN** a client makes 5 attempts, waits 60 seconds, and attempts again
- **THEN** the rate limiter returns is_allowed = True (old timestamps have expired from the window)

#### Scenario: Different IPs for same email are tracked separately
- **WHEN** two different IP addresses both attempt login for the same email
- **THEN** each IP+email combination has its own counter and is rate-limited independently

#### Scenario: Same IP for different emails are tracked separately
- **WHEN** the same IP attempts login for two different emails
- **THEN** each IP+email combination has its own counter and is rate-limited independently

### Requirement: Rate limiter resets on successful login
The system SHALL reset the rate limiter counter for a specific IP+email combination upon successful login.

#### Scenario: Successful login resets rate limit
- **WHEN** a client makes 3 failed attempts, then a successful login, then 3 more failed attempts
- **THEN** the 3 more failed attempts SHALL be allowed (the counter was reset after the successful login)

### Requirement: Rate limiting applied before credential validation
The system SHALL check the rate limiter BEFORE validating credentials during login. If rate-limited, the system SHALL return 429 Too Many Requests without performing any credential lookup.

#### Scenario: Rate limited request returns 429 before DB lookup
- **WHEN** a client exceeds the rate limit and sends a login request
- **THEN** the system returns 429 Too Many Requests WITHOUT looking up the AuthUser or verifying the password

### Requirement: Rate limiter cleanup
The system SHALL clean up expired entries from the rate limiter store to prevent unbounded memory growth.

#### Scenario: Expired entries are cleaned
- **WHEN** an IP+email combination has no login attempts within the last 60 seconds
- **THEN** the rate limiter SHALL remove that entry from its store (either inline during pruning or via periodic cleanup)
