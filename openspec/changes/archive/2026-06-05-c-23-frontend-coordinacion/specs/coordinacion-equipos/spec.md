## ADDED Requirements

### Requirement: Vista de mis equipos
El sistema SHALL mostrar al COORDINADOR/ADMIN todas las comisiones y materias donde está asignado, con rol, carrera, cohorte, vigencia y estado. La vista DEBE permitir filtrar por estado, materia, rol, carrera y cohorte.

#### Scenario: COORDINADOR ve sus equipos con filtros
- **WHEN** el COORDINADOR accede a `/coordinacion/equipos`
- **THEN** el sistema carga y muestra la lista de equipos asignados al usuario autenticado
- **AND** los filtros (estado, materia, rol, carrera, cohorte) modifican la lista sin recargar la página

#### Scenario: Equipos vacíos muestra estado informativo
- **WHEN** el usuario no tiene equipos asignados
- **THEN** el sistema muestra un mensaje "No tenés equipos asignados" con un CTA para crear asignaciones

### Requirement: Vista de asignaciones individuales
El sistema SHALL mostrar todas las asignaciones activas del tenant con filtros por materia, carrera, cohorte, docente, rol y relación de reporte.

#### Scenario: COORDINADOR consulta asignaciones del tenant
- **WHEN** el COORDINADOR accede a la vista de asignaciones individuales
- **THEN** el sistema muestra una tabla paginada con todas las asignaciones activas
- **AND** los filtros aplicados reducen los resultados en tiempo real

### Requirement: Asignación masiva de docentes
El sistema SHALL permitir seleccionar múltiples docentes y asignarlos en bloque a una combinación materia x carrera x cohorte x rol con vigencia definida, mediante un formulario multi-step.

#### Scenario: Asignación masiva exitosa
- **WHEN** el COORDINADOR completa los pasos del wizard (seleccionar materia/carrera/cohorte, seleccionar docentes, definir rol, establecer vigencia) y confirma
- **THEN** el sistema crea las asignaciones en lote y redirige a la vista de equipos con mensaje de éxito

#### Scenario: Asignación masiva con error de validación
- **WHEN** el COORDINADOR intenta confirmar sin seleccionar al menos un docente
- **THEN** el sistema muestra un error de validación "Seleccioná al menos un docente" y no permite avanzar

#### Scenario: Docente ya asignado previene duplicado
- **WHEN** un docente seleccionado ya está asignado a la misma combinación materia x cohorte x rol con vigencia activa
- **THEN** el sistema muestra un warning "El docente ya tiene una asignación activa para esta combinación" y permite decidir si continuar o no

### Requirement: Clonar equipo docente
El sistema SHALL permitir duplicar todas las asignaciones de un equipo origen (materia x carrera x cohorte) hacia un destino (misma materia x carrera x nueva cohorte), mediante un formulario de dos pasos.

#### Scenario: Clonado exitoso entre cohortes
- **WHEN** el COORDINADOR selecciona equipo origen (materia, carrera, cohorte origen), selecciona cohorte destino y confirma
- **THEN** el sistema duplica todas las asignaciones vigentes del origen en el destino y muestra resumen de asignaciones creadas

#### Scenario: Clonado sin asignaciones en origen
- **WHEN** el equipo origen no tiene asignaciones vigentes
- **THEN** el sistema muestra mensaje "El equipo origen no tiene asignaciones para clonar" y no crea ninguna asignación

### Requirement: Modificar vigencia general del equipo
El sistema SHALL permitir actualizar fechas de vigencia (desde/hasta) de todas las asignaciones de un equipo en una sola operación.

#### Scenario: Actualización de vigencia exitosa
- **WHEN** el COORDINADOR selecciona un equipo, establece nuevas fechas de vigencia y confirma
- **THEN** el sistema actualiza la vigencia de todas las asignaciones del equipo y muestra confirmación

### Requirement: Exportar equipo docente
El sistema SHALL permitir exportar el detalle de asignaciones de un equipo (docente, rol, materia, carrera, cohorte, vigencia, estado) como archivo descargable.

#### Scenario: Exportación de equipo
- **WHEN** el COORDINADOR hace clic en "Exportar" para un equipo
- **THEN** el sistema genera y descarga un archivo con el detalle de todas las asignaciones del equipo
