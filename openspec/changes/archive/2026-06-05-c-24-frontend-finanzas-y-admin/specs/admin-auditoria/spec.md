## ADDED Requirements

### Requirement: Panel de metricas de uso del sistema
El sistema SHALL mostrar un panel con metricas agregadas de actividad del sistema para supervision.

#### Scenario: Acceso al panel de auditoria
- **WHEN** un usuario con permiso `auditoria:ver` navega a `/admin/auditoria`
- **THEN** el sistema muestra:
  - Grafico o tabla de acciones por dia (volumen temporal)
  - Estado de comunicaciones agrupado por docente (Pendiente, Enviando, Enviado, Fallido, Cancelado)
  - Interacciones por docente y materia (metrica por tipo de accion)
  - Log de ultimas acciones (maximo 200 registros)
- **AND** todos los widgets tienen filtros por rango de fechas, materia y usuario

#### Scenario: Filtrado del panel por rango de fechas
- **WHEN** el usuario selecciona un rango de fechas en los filtros globales
- **THEN** todos los widgets del panel se actualizan mostrando datos solo del periodo seleccionado

#### Scenario: Panel sin datos
- **WHEN** no hay actividad registrada para los filtros seleccionados
- **THEN** cada widget muestra un estado vacio informativo

### Requirement: Log completo de auditoria
El sistema SHALL mostrar una tabla paginada con el registro completo de acciones del sistema.

#### Scenario: Acceso al log completo
- **WHEN** un usuario con permiso `auditoria:ver` navega a `/admin/auditoria/log`
- **THEN** el sistema muestra una tabla con columnas: fecha/hora, usuario, materia, accion, filas afectadas, IP, user agent
- **AND** las filas estan ordenadas por fecha/hora descendente
- **AND** soporta paginacion server-side

#### Scenario: Filtrado del log por accion
- **WHEN** el usuario selecciona un tipo de accion en el filtro (ej: "LIQUIDACION_CERRAR")
- **THEN** la tabla muestra solo registros de ese tipo de accion

#### Scenario: Log sin resultados
- **WHEN** los filtros aplicados no devuelven resultados
- **THEN** el sistema muestra: "No se encontraron registros de auditoria"
