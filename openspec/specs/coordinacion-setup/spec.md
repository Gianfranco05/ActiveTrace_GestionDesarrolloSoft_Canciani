## ADDED Requirements

### Requirement: Wizard de setup de cuatrimestre
El sistema SHALL guiar al COORDINADOR a través del flujo FL-03 de inicio de cuatrimestre mediante un wizard multi-step con pasos secuenciales: (1) crear cohorte, (2) clonar equipo docente, (3) ajustar asignaciones, (4) ajustar vigencias, (5) cargar programas, (6) cargar fechas de evaluaciones, (7) publicar aviso de bienvenida.

#### Scenario: COORDINADOR completa el setup paso a paso
- **WHEN** el COORDINADOR inicia el wizard de setup desde `/coordinacion/setup`
- **THEN** el sistema presenta el paso 1 (crear cohorte) y avanza secuencialmente al completar cada paso
- **AND** el wizard muestra progreso visual (ej. "Paso 3 de 7")

#### Scenario: Navegación entre pasos del wizard
- **WHEN** el usuario está en un paso intermedio
- **THEN** puede volver a pasos anteriores para revisar o modificar, pero no puede saltar a pasos futuros sin completar los anteriores

#### Scenario: Abandono del wizard
- **WHEN** el usuario cierra el wizard sin completar todos los pasos
- **THEN** los datos ya guardados en pasos completados persisten (ej. cohorte creada, equipo clonado)

### Requirement: Paso 1 — Crear cohorte
El sistema SHALL permitir crear una nueva cohorte con identificador, nombre, fechas de vigencia desde/hasta y estado.

#### Scenario: Creación de cohorte
- **WHEN** el COORDINADOR define el identificador (ej. "AGO-2026"), nombre, fechas de vigencia y confirma
- **THEN** el sistema crea la cohorte y habilita el paso 2

#### Scenario: Validación de identificador duplicado
- **WHEN** el COORDINADOR ingresa un identificador que ya existe en el tenant
- **THEN** el sistema muestra error "Ya existe una cohorte con ese identificador"

### Requirement: Paso 2 — Clonar equipo docente
El sistema SHALL permitir seleccionar un equipo origen (materia x carrera x cohorte) y clonarlo a la nueva cohorte creada en el paso 1.

#### Scenario: Clonado de equipo a nueva cohorte
- **WHEN** el COORDINADOR selecciona equipo origen, confirma destino (nueva cohorte) y ejecuta clonado
- **THEN** el sistema duplica todas las asignaciones vigentes y muestra resumen de cuántas asignaciones se crearon

### Requirement: Paso 3 — Ajustar asignaciones
El sistema SHALL mostrar las asignaciones de la nueva cohorte y permitir agregar docentes nuevos mediante asignación masiva.

#### Scenario: Asignación masiva de docentes nuevos
- **WHEN** el COORDINADOR usa la funcionalidad de asignación masiva para agregar docentes a la nueva cohorte
- **THEN** el sistema crea las asignaciones y las incorpora a la vista del paso 3

### Requirement: Paso 4 — Ajustar vigencias
El sistema SHALL permitir modificar las fechas de vigencia de las asignaciones de la nueva cohorte en lote.

#### Scenario: Ajuste de vigencias del equipo
- **WHEN** el COORDINADOR establece nuevas fechas de vigencia para el equipo y confirma
- **THEN** el sistema actualiza todas las asignaciones con las nuevas fechas

### Requirement: Paso 5 — Cargar programas
El sistema SHALL permitir subir el programa oficial de cada materia para la cohorte con título descriptivo.

#### Scenario: Carga de programa de materia
- **WHEN** el COORDINADOR selecciona una materia, sube un archivo de programa y define un título
- **THEN** el sistema asocia el programa a la materia x carrera x cohorte

### Requirement: Paso 6 — Cargar fechas de evaluaciones
El sistema SHALL permitir registrar fechas de parciales, trabajos prácticos y coloquios por materia, cohorte, tipo y número de instancia.

#### Scenario: Registro de fecha de parcial
- **WHEN** el COORDINADOR registra un parcial: materia, tipo "Parcial", instancia 1, fecha y título
- **THEN** el sistema guarda la fecha académica y la muestra en la tabla del paso 6

### Requirement: Paso 7 — Publicar aviso de bienvenida
El sistema SHALL permitir crear y publicar un aviso con alcance a la nueva cohorte, dirigido a roles seleccionados, anunciando el inicio del período.

#### Scenario: Publicación de aviso de bienvenida
- **WHEN** el COORDINADOR completa el formulario de aviso con alcance a la nueva cohorte, roles destinatarios, título "Bienvenida al cuatrimestre AGO-2026" y publica
- **THEN** el sistema crea el aviso y muestra resumen final "Setup completado"
