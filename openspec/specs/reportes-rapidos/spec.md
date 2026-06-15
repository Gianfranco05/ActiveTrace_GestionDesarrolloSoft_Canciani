## ADDED Requirements

### Requirement: Métricas clave de la materia

El sistema SHALL mostrar una vista consolidada con métricas clave de la materia: total de alumnos, total de actividades, tasa de aprobación general, promedio de nota, y cantidad de alumnos atrasados.

#### Scenario: Vista de métricas con datos
- **WHEN** el usuario accede a reportes rápidos con calificaciones importadas
- **THEN** se muestran cards con cada métrica calculada (total alumnos, tasa de aprobación, promedio, atrasados)

#### Scenario: Vista sin datos importados
- **WHEN** el usuario accede a reportes rápidos sin haber importado calificaciones
- **THEN** el sistema muestra un estado informativo indicando que debe importar datos primero

### Requirement: Tendencia de aprobación por actividad

El sistema SHALL mostrar un indicador visual de la tasa de aprobación por cada actividad seleccionada.

#### Scenario: Tasas de aprobación por actividad
- **WHEN** se muestran los reportes con actividades seleccionadas
- **THEN** cada actividad muestra su porcentaje de alumnos que la aprobaron, con una barra de progreso visual

### Requirement: Acceso directo a otras vistas

El sistema SHALL proveer enlaces o botones de acceso rápido desde los reportes hacia las vistas de atrasados y ranking.

#### Scenario: Navegación desde reportes a atrasados
- **WHEN** el usuario hace clic en "Ver atrasados" desde la card de alumnos atrasados
- **THEN** el sistema navega a la vista de atrasados para la misma materia
