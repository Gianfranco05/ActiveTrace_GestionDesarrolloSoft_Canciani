# finanzas-facturas Specification

## Purpose
Frontend de gestion de facturas: listado con filtros, carga de factura con archivo PDF y cambio de estado Pendiente/Abonada. Vista para usuarios con permiso `facturas:gestionar`.

## ADDED Requirements

### Requirement: Listado de facturas con filtros
El sistema SHALL mostrar una tabla paginada de facturas cargadas con filtros por docente, estado y rango de fechas.

#### Scenario: Acceso a gestion de facturas
- **WHEN** un usuario con permiso `facturas:gestionar` navega a `/finanzas/facturas`
- **THEN** el sistema muestra una tabla con columnas: docente, periodo, detalle, archivo (nombre + tamaño), estado, fecha de carga
- **AND** filtros disponibles: docente, estado (Pendiente/Abonada), rango de fechas
- **AND** busqueda libre por texto

#### Scenario: Filtrar por estado pendiente
- **WHEN** el usuario selecciona el filtro "Pendiente"
- **THEN** la tabla muestra solo facturas en estado Pendiente

### Requirement: Carga de factura con archivo adjunto
El sistema SHALL permitir cargar una nueva factura con archivo PDF adjunto y metadatos asociados.

#### Scenario: Carga exitosa de factura
- **WHEN** el usuario completa el formulario con docente, periodo (AAAA-MM), detalle y archivo PDF
- **AND** el archivo PDF no supera 10 MB
- **AND** hace submit
- **THEN** el sistema crea la factura en estado Pendiente
- **AND** muestra confirmacion visual
- **AND** la tabla se actualiza

#### Scenario: Archivo excede tamaño maximo
- **WHEN** el usuario selecciona un archivo mayor a 10 MB
- **THEN** el sistema muestra un error de validacion antes del submit: "El archivo no puede superar 10 MB"

#### Scenario: Archivo no es PDF
- **WHEN** el usuario selecciona un archivo que no es PDF
- **THEN** el sistema muestra un error de validacion: "Solo se permiten archivos PDF"

### Requirement: Cambio de estado de factura
El sistema SHALL permitir cambiar el estado de una factura entre Pendiente y Abonada.

#### Scenario: Marcar factura como abonada
- **WHEN** el usuario hace click en "Marcar como abonada" sobre una factura en estado Pendiente
- **THEN** el sistema cambia el estado a Abonada
- **AND** registra la fecha de abono
- **AND** muestra confirmacion

#### Scenario: Revertir factura a pendiente
- **WHEN** el usuario hace click en "Marcar como pendiente" sobre una factura en estado Abonada
- **THEN** el sistema cambia el estado a Pendiente
- **AND** limpia la fecha de abono
