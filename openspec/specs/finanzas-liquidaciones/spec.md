# finanzas-liquidaciones Specification

## Purpose
Frontend de liquidaciones de honorarios: vista segmentada (General/NEXO/Factura), KPIs de cabecera, cierre de liquidacion e historial. Vista para usuarios con permisos `liquidaciones:ver` y `liquidaciones:cerrar`.

## ADDED Requirements

### Requirement: Vista de liquidaciones del periodo con segmentacion
El sistema SHALL mostrar una vista de liquidaciones de honorarios docentes para un periodo seleccionado, segmentada en tres pestañas: General, NEXO y Factura. La vista incluye KPIs de cabecera con totales.

#### Scenario: Usuario FINANZAS accede a la vista de liquidaciones
- **WHEN** un usuario con permiso `liquidaciones:ver` navega a `/finanzas/liquidaciones`
- **THEN** el sistema muestra KPIs de cabecera (total general, total NEXO, total facturas, docentes activos)
- **AND** muestra una tabla segmentada con pestañas General, NEXO y Factura
- **AND** cada fila de la tabla General muestra docente, rol, comisiones, monto base, monto plus y total
- **AND** la pestaña NEXO muestra solo docentes con `es_nexo = true`
- **AND** la pestaña Factura muestra solo docentes con `excluido_por_factura = true`

#### Scenario: Filtrado por cohorte y mes
- **WHEN** el usuario selecciona una cohorte y un mes en los filtros
- **THEN** la tabla y KPIs se recalculan mostrando solo los datos del periodo y cohorte seleccionados

#### Scenario: Sin datos en el periodo
- **WHEN** no existen liquidaciones para el periodo y filtros seleccionados
- **THEN** el sistema muestra un estado vacio informativo: "No hay liquidaciones para este periodo"

### Requirement: Cerrar liquidacion
El sistema SHALL permitir a un usuario con permiso `liquidaciones:cerrar` inmutabilizar una liquidacion de un periodo, impidiendo modificaciones posteriores.

#### Scenario: Cierre exitoso de liquidacion
- **WHEN** un usuario con permiso `liquidaciones:cerrar` confirma el cierre de una liquidacion en estado Abierta
- **THEN** el sistema cambia el estado a Cerrada
- **AND** muestra confirmacion visual de exito
- **AND** deshabilita cualquier accion de modificacion sobre esa liquidacion

#### Scenario: Intento de cierre sin permiso
- **WHEN** un usuario sin permiso `liquidaciones:cerrar` intenta cerrar una liquidacion
- **THEN** el boton de cierre no se renderiza

#### Scenario: Confirmacion antes de cerrar
- **WHEN** el usuario hace click en "Cerrar liquidacion"
- **THEN** el sistema muestra un dialogo de confirmacion advirtiendo que la accion es irreversible
- **AND** solo ejecuta el cierre si el usuario confirma

### Requirement: Historial de liquidaciones
El sistema SHALL mostrar una tabla paginada con el historial de liquidaciones cerradas de periodos anteriores.

#### Scenario: Acceso al historial
- **WHEN** un usuario con permiso `liquidaciones:ver` navega a `/finanzas/liquidaciones/historial`
- **THEN** el sistema muestra una tabla con columnas: periodo, cohorte, total liquidado, cantidad de docentes, fecha de cierre
- **AND** las filas estan ordenadas por fecha de cierre descendente

#### Scenario: Historial vacio
- **WHEN** no hay liquidaciones cerradas previas
- **THEN** el sistema muestra un estado vacio: "No hay liquidaciones cerradas"
