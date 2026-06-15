# admin-estructura-academica Specification

## Purpose
Frontend de gestion de estructura academica: ABM de carreras, cohortes y materias del tenant. Vista para usuarios con permiso `estructura:gestionar`.

## ADDED Requirements

### Requirement: ABM de carreras
El sistema SHALL permitir a usuarios con permiso `estructura:gestionar` crear, editar y cambiar el estado (activa/inactiva) de carreras.

#### Scenario: Listar carreras
- **WHEN** un usuario con permiso `estructura:gestionar` accede a la seccion de estructura academica
- **THEN** el sistema muestra una tabla de carreras con columnas: codigo, nombre, estado
- **AND** las carreras activas e inactivas se diferencian visualmente

#### Scenario: Crear nueva carrera
- **WHEN** el usuario completa el formulario con codigo y nombre
- **AND** hace submit
- **THEN** el sistema crea la carrera en estado Activa
- **AND** muestra confirmacion

#### Scenario: Editar carrera existente
- **WHEN** el usuario modifica el codigo o nombre de una carrera existente
- **AND** hace submit
- **THEN** el sistema actualiza el registro

### Requirement: ABM de cohortes
El sistema SHALL permitir crear, editar y cambiar el estado de cohortes asociadas a una carrera, con fechas de vigencia.

#### Scenario: Listar cohortes
- **WHEN** el usuario selecciona una carrera
- **THEN** el sistema muestra las cohortes asociadas con columnas: nombre, año de inicio, desde, hasta, estado

#### Scenario: Crear nueva cohorte
- **WHEN** el usuario completa el formulario con nombre, año de inicio, fechas desde/hasta
- **AND** hace submit
- **THEN** el sistema crea la cohorte asociada a la carrera seleccionada

### Requirement: ABM de materias
El sistema SHALL permitir crear, editar y cambiar el estado de materias del tenant.

#### Scenario: Listar materias
- **WHEN** el usuario accede a la seccion de materias
- **THEN** el sistema muestra una tabla con columnas: nombre, codigo, estado
- **AND** permite busqueda por nombre o codigo

#### Scenario: Crear nueva materia
- **WHEN** el usuario completa el formulario con nombre y codigo
- **AND** hace submit
- **THEN** el sistema crea la materia y la agrega a la tabla
