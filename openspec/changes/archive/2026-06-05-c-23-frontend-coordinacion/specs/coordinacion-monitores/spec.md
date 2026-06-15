## ADDED Requirements

### Requirement: Monitor general de actividades (F2.7)
El sistema SHALL mostrar vista transversal de todos los alumnos del tenant con su estado de actividades. DEBE incluir filtros por materia, regional, comisión, búsqueda libre por alumno, estado de actividad y criterio de clasificación.

#### Scenario: COORDINADOR consulta monitor general
- **WHEN** el COORDINADOR accede a `/coordinacion/monitores`
- **THEN** el sistema carga el monitor general con tabla paginada de alumnos y su estado de actividades
- **AND** los filtros (materia, regional, comisión, búsqueda, estado) modifican los resultados sin recargar

#### Scenario: Aplicar y limpiar filtros
- **WHEN** el usuario aplica filtros y luego presiona "Limpiar filtros"
- **THEN** el sistema restablece todos los filtros a su valor por defecto y recarga los datos

#### Scenario: Exportar datos del monitor
- **WHEN** el usuario hace clic en "Exportar"
- **THEN** el sistema genera y descarga un archivo con los datos visibles según los filtros aplicados

### Requirement: Monitor de seguimiento por docente (F2.9)
El sistema SHALL mostrar vista filtrable del estado de actividades de alumnos con filtros adicionales de rango de fechas para acotar el período de análisis.

#### Scenario: COORDINADOR consulta seguimiento con rango de fechas
- **WHEN** el COORDINADOR accede al monitor de seguimiento por docente y aplica rango de fechas
- **THEN** el sistema muestra solo las actividades dentro del período seleccionado, filtrables por docente, alumno, correo, comisión, regional y materia

#### Scenario: Filtro por mínimo de actividades cumplidas
- **WHEN** el usuario establece un filtro de "mínimo de actividades cumplidas"
- **THEN** el sistema muestra solo alumnos que cumplen o superan ese umbral

### Requirement: Dashboard de coordinación con KPIs
El sistema SHALL mostrar en la landing de coordinación un dashboard con tarjetas de acceso rápido a cada módulo y KPIs resumidos de monitores.

#### Scenario: COORDINADOR ve dashboard de coordinación
- **WHEN** el COORDINADOR accede a `/coordinacion`
- **THEN** el sistema muestra un dashboard con cards navegables (Equipos, Avisos, Tareas, Encuentros, Coloquios, Monitores, Setup) y KPIs resumidos (ej. tareas pendientes, avisos activos, próximos encuentros)
