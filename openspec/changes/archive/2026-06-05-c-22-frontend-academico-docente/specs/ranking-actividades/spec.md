## ADDED Requirements

### Requirement: Ranking de actividades aprobadas

El sistema SHALL mostrar una tabla ordenada descendentemente por cantidad de actividades aprobadas por alumno, incluyendo solo alumnos con al menos una actividad aprobada.

#### Scenario: Ranking con múltiples alumnos
- **WHEN** el usuario accede a la vista de ranking con datos cargados
- **THEN** la tabla muestra los alumnos ordenados de mayor a menor cantidad de actividades aprobadas

#### Scenario: Empate en cantidad de aprobadas
- **WHEN** dos alumnos tienen la misma cantidad de actividades aprobadas
- **THEN** el orden entre ellos es alfabético por nombre

#### Scenario: Sin actividades aprobadas
- **WHEN** ningún alumno tiene actividades aprobadas
- **THEN** el sistema muestra un mensaje indicando que no hay datos de ranking disponibles

### Requirement: Detalle por alumno en ranking

El sistema SHALL mostrar para cada alumno en el ranking: nombre, cantidad de actividades aprobadas, total de actividades, y porcentaje de aprobación.

#### Scenario: Visualización de detalle
- **WHEN** se muestra el ranking
- **THEN** cada fila incluye nombre del alumno, X/Y actividades aprobadas, y porcentaje calculado
