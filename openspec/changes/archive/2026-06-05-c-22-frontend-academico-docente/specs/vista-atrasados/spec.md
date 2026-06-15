## ADDED Requirements

### Requirement: Visualización de alumnos atrasados

El sistema SHALL mostrar una tabla de alumnos atrasados para la materia seleccionada, donde "atrasado" se define como alumno con actividades faltantes o con calificación por debajo del umbral configurado.

#### Scenario: Tabla con alumnos atrasados
- **WHEN** el usuario accede a la vista de atrasados con datos cargados
- **THEN** la tabla muestra cada alumno con: nombre, estado de actividades, cantidad de actividades faltantes, y porcentaje de aprobación

#### Scenario: Sin alumnos atrasados
- **WHEN** todos los alumnos tienen todas las actividades aprobadas sobre el umbral
- **THEN** el sistema muestra un mensaje indicando que no hay alumnos atrasados

#### Scenario: Sin datos importados
- **WHEN** el usuario accede a la vista de atrasados sin haber importado calificaciones
- **THEN** el sistema muestra un estado informativo indicando que primero debe importar calificaciones

### Requirement: Selección de alumnos para comunicación

El sistema SHALL permitir seleccionar uno o más alumnos atrasados de la tabla para iniciar el flujo de comunicación.

#### Scenario: Selección múltiple de alumnos
- **WHEN** el usuario selecciona 3 alumnos de la tabla y hace clic en "Comunicar"
- **THEN** el sistema navega a la página de comunicaciones con los alumnos preseleccionados

#### Scenario: Selección de todos los alumnos
- **WHEN** el usuario hace clic en "Seleccionar todos" en la cabecera de la tabla
- **THEN** todos los alumnos visibles quedan seleccionados

### Requirement: Filtros de la vista de atrasados

El sistema SHALL permitir filtrar la tabla de atrasados por cantidad mínima de actividades faltantes y por porcentaje máximo de aprobación.

#### Scenario: Filtro por actividades faltantes
- **WHEN** el usuario filtra por "al menos 2 actividades faltantes"
- **THEN** la tabla muestra solo los alumnos con 2 o más actividades faltantes
