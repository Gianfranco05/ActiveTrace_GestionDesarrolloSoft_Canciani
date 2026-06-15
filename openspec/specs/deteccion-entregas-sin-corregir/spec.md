## ADDED Requirements

### Requirement: Importación de reporte de finalización del LMS

El sistema SHALL permitir al PROFESOR subir un archivo exportado del LMS con el estado de finalización de actividades por alumno para detectar entregas sin calificación registrada.

#### Scenario: Upload de reporte de finalización
- **WHEN** el usuario sube un archivo de reporte de finalización del LMS
- **THEN** el sistema procesa el archivo y cruza con las calificaciones existentes

#### Scenario: Reporte sin calificaciones previas
- **WHEN** el usuario sube un reporte de finalización sin haber importado calificaciones antes
- **THEN** el sistema muestra un aviso indicando que necesita importar calificaciones primero para hacer el cruce

### Requirement: Tabla de entregas sin corregir

El sistema SHALL mostrar una tabla con las actividades que figuran como entregadas en el LMS pero que no tienen calificación registrada, identificadas por alumno y actividad.

#### Scenario: Entregas sin corregir detectadas
- **WHEN** el cruce de datos detecta 5 entregas sin calificar
- **THEN** la tabla muestra para cada entrega: nombre del alumno, actividad, fecha de entrega (si disponible), y estado "Sin corregir"

#### Scenario: Sin entregas pendientes
- **WHEN** todas las entregas del reporte tienen calificación registrada
- **THEN** el sistema muestra un mensaje indicando que no hay entregas pendientes de corrección

### Requirement: Exportación del listado de entregas sin corregir

El sistema SHALL permitir exportar el listado de entregas sin corregir a un archivo descargable.

#### Scenario: Exportación del listado
- **WHEN** el usuario hace clic en "Exportar" con entregas sin corregir detectadas
- **THEN** el sistema descarga un archivo con el listado completo de entregas pendientes
