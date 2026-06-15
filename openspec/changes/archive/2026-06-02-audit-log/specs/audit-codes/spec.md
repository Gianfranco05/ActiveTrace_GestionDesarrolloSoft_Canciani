## ADDED Requirements

### Requirement: AuditAction enum
The system SHALL define an `AuditAction` enum in `core/audit_codes.py` that extends `str` and `Enum`. The enum SHALL contain the following members:

| Member | Value |
|--------|-------|
| `CALIFICACIONES_IMPORTAR` | `"CALIFICACIONES_IMPORTAR"` |
| `PADRON_CARGAR` | `"PADRON_CARGAR"` |
| `COMUNICACION_ENVIAR` | `"COMUNICACION_ENVIAR"` |
| `ASIGNACION_MODIFICAR` | `"ASIGNACION_MODIFICAR"` |
| `LIQUIDACION_CERRAR` | `"LIQUIDACION_CERRAR"` |
| `IMPERSONACION_INICIAR` | `"IMPERSONACION_INICIAR"` |
| `IMPERSONACION_FINALIZAR` | `"IMPERSONACION_FINALIZAR"` |

#### Scenario: Enum member values match constants
- **WHEN** accessing any AuditAction member
- **THEN** its value SHALL equal its name (e.g., `AuditAction.CALIFICACIONES_IMPORTAR.value == "CALIFICACIONES_IMPORTAR"`)

#### Scenario: Enum is iterable
- **WHEN** iterating over AuditAction
- **THEN** all 7 members SHALL be present

#### Scenario: Invalid action string raises ValueError
- **WHEN** calling `AuditAction("INVALID_ACTION")`
- **THEN** a ValueError SHALL be raised
