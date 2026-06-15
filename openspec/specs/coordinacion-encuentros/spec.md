## ADDED Requirements

### Requirement: Vista admin de encuentros
El sistema SHALL mostrar al COORDINADOR/ADMIN la vista transversal de todos los encuentros del tenant, independientemente del docente que los creó.

#### Scenario: COORDINADOR ve todos los encuentros
- **WHEN** el COORDINADOR accede a `/coordinacion/encuentros`
- **THEN** el sistema carga la lista de encuentros de todo el tenant con filtros por materia, docente, estado y rango de fechas
- **AND** cada encuentro muestra fecha, horario, materia, docente creador, enlace y estado

### Requirement: Crear encuentro recurrente
El sistema SHALL permitir crear un slot de encuentro con periodicidad semanal: materia, día de la semana, horario, fecha de inicio, cantidad de semanas, título y enlace de videoconferencia. El sistema DEBE generar automáticamente todas las instancias.

#### Scenario: Creación de serie recurrente
- **WHEN** el COORDINADOR configura una serie recurrente (ej. todos los lunes 18:00 por 12 semanas) y confirma
- **THEN** el sistema crea 12 instancias de encuentro, una por cada lunes a las 18:00

#### Scenario: Validación de cantidad de semanas
- **WHEN** el COORDINADOR ingresa 0 o un valor negativo en cantidad de semanas
- **THEN** el sistema muestra error de validación "La cantidad de semanas debe ser mayor a 0"

### Requirement: Crear encuentro único
El sistema SHALL permitir crear una instancia de encuentro para fecha y hora específicas sin recurrencia.

#### Scenario: Creación de encuentro único
- **WHEN** el COORDINADOR define fecha, horario, título y enlace, y confirma
- **THEN** el sistema crea una única instancia de encuentro

### Requirement: Editar instancia de encuentro
El sistema SHALL permitir modificar estado, enlace de videoconferencia, enlace de grabación y comentario interno de una instancia existente.

#### Scenario: COORDINADOR registra grabación post-encuentro
- **WHEN** el COORDINADOR edita una instancia, pega la URL de la grabación y guarda
- **THEN** el sistema actualiza la instancia con el enlace de grabación

### Requirement: Generar contenido para aula virtual
El sistema SHALL generar un fragmento de contenido formateado con los encuentros programados, listo para copiar al aula virtual del LMS.

#### Scenario: Generación de contenido para LMS
- **WHEN** el COORDINADOR selecciona "Generar contenido para aula virtual" para una materia
- **THEN** el sistema muestra un bloque de texto formateado con los encuentros y sus enlaces, con botón para copiar al portapapeles
