## ADDED Requirements

### Requirement: Panel de métricas de coloquios
El sistema SHALL mostrar al COORDINADOR/ADMIN un panel con métricas: total de alumnos cargados, instancias activas, reservas activas y notas registradas.

#### Scenario: Visualización de métricas de coloquios
- **WHEN** el COORDINADOR accede a `/coordinacion/coloquios`
- **THEN** el sistema muestra un dashboard con cards de métricas (alumnos, instancias, reservas, notas) y un listado de convocatorias debajo

### Requirement: Listado de convocatorias
El sistema SHALL mostrar tabla de convocatorias activas con: materia, instancia, días disponibles, convocados, reservas activas, cupos libres y acciones de gestión.

#### Scenario: COORDINADOR ve convocatorias activas
- **WHEN** el COORDINADOR accede al listado de convocatorias
- **THEN** el sistema muestra tabla paginada con métricas por convocatoria y botones de acción (editar, importar alumnos, cerrar)

### Requirement: Crear convocatoria de coloquio
El sistema SHALL permitir crear una convocatoria definiendo: materia, nombre de instancia, días y cupos disponibles.

#### Scenario: Creación de convocatoria con días y cupos
- **WHEN** el COORDINADOR crea una convocatoria definiendo materia, "Coloquio Final", 3 días con cupos de 10 alumnos cada uno
- **THEN** el sistema crea la convocatoria y genera los turnos reservables con sus cupos

#### Scenario: Validación de cupos positivos
- **WHEN** el COORDINADOR ingresa cupo 0 o negativo para un día
- **THEN** el sistema muestra error "El cupo debe ser mayor a 0"

### Requirement: Importar alumnos a convocatoria
El sistema SHALL permitir cargar o actualizar el padrón de alumnos habilitados para una convocatoria mediante importación de archivo.

#### Scenario: Importación de alumnos a convocatoria
- **WHEN** el COORDINADOR selecciona una convocatoria, sube un archivo con el padrón de alumnos y confirma
- **THEN** el sistema actualiza la lista de alumnos habilitados para esa convocatoria

### Requirement: Agenda de reservas activas
El sistema SHALL mostrar la agenda consolidada de reservas activas de todas las convocatorias, con filtros por materia, convocatoria y día.

#### Scenario: Visualización de agenda de reservas
- **WHEN** el COORDINADOR accede a la agenda de reservas
- **THEN** el sistema muestra todas las reservas activas con alumno, día, horario y estado

### Requirement: Registro académico de resultados
El sistema SHALL mostrar el registro consolidado de resultados de coloquio con notas finales.

#### Scenario: Consulta de registro académico
- **WHEN** el COORDINADOR consulta el registro académico de coloquios
- **THEN** el sistema muestra tabla con alumno, materia, instancia, nota y fecha de registro
