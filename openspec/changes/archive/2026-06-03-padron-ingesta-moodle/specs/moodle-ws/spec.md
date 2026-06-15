## ADDED Requirements

### Requirement: Moodle WS client — get_enrolled_users

The system SHALL provide a MoodleWSClient in `backend/app/integrations/moodle_ws.py` that connects to a Moodle instance via Web Services API. For C-09, the client SHALL implement a single method: `get_enrolled_users()`. The client SHALL be mockable for tests.

#### Scenario: Get enrolled users returns student list
- **GIVEN** a configured MoodleWSClient with valid base_url and token
- **WHEN** calling get_enrolled_users(materia_id, cohorte_id)
- **THEN** the response SHALL be a list of MoodleStudent dataclass instances with nombre, apellidos, email
- **AND** comision and regional SHALL be included if available from Moodle

#### Scenario: Moodle connection error
- **GIVEN** a MoodleWSClient with an unreachable base_url
- **WHEN** calling get_enrolled_users()
- **THEN** a MoodleConnectionError SHALL be raised

#### Scenario: Moodle auth error (invalid token)
- **GIVEN** a MoodleWSClient with an invalid token
- **WHEN** calling get_enrolled_users()
- **THEN** a MoodleAuthError SHALL be raised

#### Scenario: Moodle timeout
- **GIVEN** a MoodleWSClient with a server that does not respond within timeout
- **WHEN** calling get_enrolled_users()
- **THEN** a MoodleConnectionError SHALL be raised

#### Scenario: Client is mockable
- **GIVEN** a test that needs to simulate Moodle responses
- **WHEN** injecting a mock or stub of MoodleWSClient
- **THEN** the import service SHALL accept any object implementing the MoodleWSClient protocol

### Requirement: MoodleWSClient Protocol

The system SHALL define a Protocol class for the Moodle WS client to enable dependency injection and mocking:

```python
class MoodleWSClientProtocol(Protocol):
    async def get_enrolled_users(
        self, materia_id: str, cohorte_id: str
    ) -> list[MoodleStudent]:
        ...
```

The import service SHALL accept `MoodleWSClientProtocol` as a dependency. Production wiring provides the real implementation; test wiring provides a mock.

### Requirement: Fallback to manual import

When Moodle is unavailable (connection error, auth error, or timeout), the import service SHALL NOT fail the entire operation. Instead, it SHALL:
1. Log the error
2. Return an indicator that Moodle is unavailable
3. The user can still import via file upload (manual fallback)

#### Scenario: Moodle unavailable falls back gracefully
- **GIVEN** a MoodleWSClient that raises MoodleConnectionError
- **WHEN** the import service checks for Moodle availability
- **THEN** it SHALL return a status indicator "moodle_unavailable"
- **AND** the user SHALL still be able to import via file upload
