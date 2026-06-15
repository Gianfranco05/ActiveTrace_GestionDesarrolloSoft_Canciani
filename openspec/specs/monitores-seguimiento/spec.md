## ADDED Requirements

### Requirement: Monitor de seguimiento para tutor/profesor

El sistema SHALL mostrar una vista filtrable del estado de actividades de los alumnos asignados al usuario, con filtros por alumno, correo, comisión, regional, actividad y mínimo de actividad cumplida.

#### Scenario: Monitor con datos de alumnos asignados
- **WHEN** un PROFESOR accede al monitor de seguimiento
- **THEN** la tabla muestra solo los alumnos de las materias donde el profesor tiene asignación vigente

#### Scenario: Filtro por alumno específico
- **WHEN** el usuario escribe un nombre en el campo de búsqueda de alumno
- **THEN** la tabla se filtra mostrando solo los alumnos cuyo nombre coincide con la búsqueda

#### Scenario: Filtro por mínimo de actividades cumplidas
- **WHEN** el usuario selecciona "mínimo 3 actividades cumplidas"
- **THEN** la tabla muestra solo los alumnos que completaron al menos 3 actividades

### Requirement: Monitor de seguimiento para coordinación/admin

El sistema SHALL extender el monitor con un filtro adicional de rango de fechas para acotar el período de análisis.

#### Scenario: Filtro por rango de fechas
- **WHEN** un COORDINADOR accede al monitor y selecciona un rango de fechas "01/03/2026 - 31/05/2026"
- **THEN** la tabla muestra solo las actividades cuyo período cae dentro de ese rango

#### Scenario: Monitor sin filtro de fechas
- **WHEN** un COORDINADOR accede al monitor sin seleccionar rango de fechas
- **THEN** la tabla muestra todas las actividades sin restricción temporal

### Requirement: Exportación del monitor

El sistema SHALL permitir exportar los datos visibles en el monitor a un archivo descargable.

#### Scenario: Exportación de datos filtrados
- **WHEN** el usuario aplica filtros y hace clic en "Exportar"
- **THEN** el archivo descargado contiene solo los datos que cumplen con los filtros aplicados
