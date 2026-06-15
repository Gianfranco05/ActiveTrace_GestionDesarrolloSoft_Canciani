## ADDED Requirements

### Requirement: Notas finales agrupadas por alumno

El sistema SHALL mostrar una tabla con la nota final calculada para cada alumno, basada en las actividades seleccionadas durante la importación.

#### Scenario: Notas finales con datos completos
- **WHEN** el usuario accede a la vista de notas finales con calificaciones importadas
- **THEN** la tabla muestra cada alumno con su nota final calculada y el detalle de actividades que la componen

#### Scenario: Sin actividades seleccionadas
- **WHEN** el usuario accede a notas finales sin haber seleccionado actividades
- **THEN** el sistema muestra un mensaje informativo indicando que debe importar y seleccionar actividades primero

### Requirement: Exportación de notas finales

El sistema SHALL permitir exportar la tabla de notas finales a un archivo descargable (.xlsx o .csv).

#### Scenario: Exportación exitosa
- **WHEN** el usuario hace clic en "Exportar" con datos visibles en la tabla
- **THEN** el sistema descarga un archivo con los datos de notas finales en el formato seleccionado

#### Scenario: Exportación sin datos
- **WHEN** el usuario hace clic en "Exportar" sin datos en la tabla
- **THEN** el botón de exportar está deshabilitado
