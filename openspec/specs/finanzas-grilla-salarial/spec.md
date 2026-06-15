# finanzas-grilla-salarial Specification

## Purpose
Frontend de gestion de grilla salarial: ABM de SalarioBase y SalarioPlus con vigencia temporal. Vista para usuarios con permiso `liquidaciones:configurar-salarios`.

## ADDED Requirements

### Requirement: ABM de SalarioBase
El sistema SHALL permitir a usuarios con permiso `liquidaciones:configurar-salarios` crear, editar y desactivar registros de SalarioBase con vigencia temporal.

#### Scenario: Listar SalarioBase
- **WHEN** un usuario con permiso `liquidaciones:configurar-salarios` accede a la seccion de grilla salarial
- **THEN** el sistema muestra una tabla con columnas: rol, monto, desde, hasta
- **AND** los registros vigentes (hasta nulo o futuro) se destacan visualmente

#### Scenario: Crear nuevo SalarioBase
- **WHEN** el usuario completa el formulario con rol, monto, fecha desde y opcionalmente fecha hasta
- **AND** hace submit
- **THEN** el sistema crea el registro y muestra confirmacion
- **AND** la tabla se actualiza con el nuevo registro

#### Scenario: Validacion de solapamiento de vigencias
- **WHEN** el usuario intenta crear un SalarioBase cuyo rango de fechas se solapa con uno existente del mismo rol
- **THEN** el sistema muestra un error de validacion: "Ya existe un salario base vigente para este rol en ese periodo"

### Requirement: ABM de SalarioPlus
El sistema SHALL permitir a usuarios con permiso `liquidaciones:configurar-salarios` crear, editar y desactivar registros de SalarioPlus con clave de grupo, rol y vigencia temporal.

#### Scenario: Listar SalarioPlus
- **WHEN** un usuario accede a la seccion de plus salariales
- **THEN** el sistema muestra una tabla con columnas: grupo, rol, descripcion, monto, desde, hasta

#### Scenario: Crear nuevo SalarioPlus
- **WHEN** el usuario completa el formulario con grupo, rol, descripcion, monto, fecha desde y opcionalmente fecha hasta
- **AND** hace submit
- **THEN** el sistema crea el registro y muestra confirmacion
- **AND** la tabla se actualiza

#### Scenario: Editar SalarioPlus existente
- **WHEN** el usuario modifica el monto o la vigencia de un SalarioPlus existente
- **AND** hace submit
- **THEN** el sistema actualiza el registro y muestra confirmacion
