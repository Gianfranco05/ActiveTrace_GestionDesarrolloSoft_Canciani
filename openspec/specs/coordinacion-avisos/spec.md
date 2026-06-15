## ADDED Requirements

### Requirement: Listado de avisos
El sistema SHALL mostrar al COORDINADOR/ADMIN el listado de avisos del tenant con filtros por estado (activo/inactivo), alcance, materia, cohorte y búsqueda por título.

#### Scenario: COORDINADOR ve listado de avisos
- **WHEN** el COORDINADOR accede a `/coordinacion/avisos`
- **THEN** el sistema carga la lista paginada de avisos ordenados por prioridad descendente
- **AND** muestra badges de estado (activo/inactivo), severidad y cantidad de acuses de recibo

#### Scenario: Filtrado de avisos por estado y alcance
- **WHEN** el usuario aplica filtros de estado y alcance
- **THEN** el sistema actualiza la lista mostrando solo los avisos que coinciden

### Requirement: Crear aviso
El sistema SHALL permitir crear un aviso con: título, cuerpo (formato enriquecido), alcance (global/materia/cohorte), roles destinatarios, severidad, ventana de visibilidad (inicio/fin), prioridad, estado activo/inactivo y requerimiento de confirmación.

#### Scenario: Creación de aviso global exitosa
- **WHEN** el COORDINADOR completa el formulario con alcance global, roles destinatarios, título, cuerpo, severidad y publica
- **THEN** el sistema crea el aviso y redirige al listado con mensaje "Aviso publicado correctamente"

#### Scenario: Creación de aviso con confirmación requerida
- **WHEN** el COORDINADOR marca "Requiere confirmación" y publica
- **THEN** el aviso se crea con `require_ack = true` y los destinatarios deberán acusar recibo

#### Scenario: Validación de campos obligatorios
- **WHEN** el COORDINADOR intenta publicar sin título o sin seleccionar roles destinatarios
- **THEN** el sistema muestra errores de validación en los campos correspondientes

### Requirement: Editar aviso
El sistema SHALL permitir modificar todos los campos de un aviso existente, incluyendo estado activo/inactivo.

#### Scenario: Edición de aviso y cambio de estado
- **WHEN** el COORDINADOR edita un aviso activo, lo marca como inactivo y guarda
- **THEN** el sistema actualiza el aviso y deja de mostrarse a los destinatarios

### Requirement: Eliminar aviso
El sistema SHALL permitir eliminar un aviso con confirmación previa.

#### Scenario: Eliminación de aviso con confirmación
- **WHEN** el COORDINADOR hace clic en eliminar y confirma en el diálogo
- **THEN** el sistema elimina el aviso y lo remueve del listado

### Requirement: Vista de acuses de recibo (acknowledgment)
El sistema SHALL mostrar para cada aviso que requiere confirmación el contador de acuses y la lista de destinatarios que confirmaron/pendientes.

#### Scenario: Consulta de acuses de un aviso
- **WHEN** el COORDINADOR consulta los acuses de un aviso con `require_ack = true`
- **THEN** el sistema muestra el total de confirmaciones sobre el total de destinatarios y el detalle de quiénes confirmaron
