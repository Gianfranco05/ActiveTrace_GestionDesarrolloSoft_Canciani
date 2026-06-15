## 1. Catálogo de permisos y código de auditoría

- [x] 1.1 Agregar `LIQUIDACION_CERRAR` al enum de códigos de auditoría en `backend/app/core/audit_codes.py`
- [x] 1.2 Agregar permisos `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:exportar`, `liquidaciones:configurar-salarios` al catálogo de permisos en `backend/app/core/permissions.py`
- [x] 1.3 Ejecutar el seed de permisos para registrar los nuevos permisos en la tabla `permiso`

## 2. Modelos ORM

- [x] 2.1 Crear `backend/app/models/liquidacion.py` con modelos `SalarioBase`, `SalarioPlus`, `GrupoMateria`, `Liquidacion`, `Factura`, todos extendiendo `BaseModelMixin` + `Base`
- [x] 2.2 Definir `__table_args__` con `UniqueConstraint` para: `(tenant_id, rol)` en SalarioBase, `(tenant_id, grupo, rol)` en SalarioPlus, `(tenant_id, grupo, materia_id)` en GrupoMateria, `(tenant_id, cohorte_id, periodo, usuario_id)` en Liquidacion
- [x] 2.3 Exportar todos los modelos nuevos en `backend/app/models/__init__.py`

## 3. Migración Alembic

- [x] 3.1 Generar migración `0NN_liquidaciones_y_honorarios.py` con 5 tablas: `salario_base`, `salario_plus`, `grupo_materia`, `liquidacion`, `factura`
- [x] 3.2 Agregar índices: `(cohorte_id, periodo)`, `(usuario_id)`, `(estado)` en liquidacion; `(usuario_id, periodo)`, `(estado)` en factura
- [x] 3.3 Crear partial unique indexes con `op.create_index(unique=True, postgresql_where=sa.text("deleted_at IS NULL"))` para las 4 tablas (salario_base, salario_plus, grupo_materia, liquidacion). NO usar UniqueConstraint en los modelos ORM — la unicidad se fuerza solo a nivel DB. Ver design D11 para la sintaxis exacta.
- [x] 3.4 Verificar que la migración `upgrade` y `downgrade` corren sin errores

## 4. Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/liquidacion.py` con schemas para SalarioBase (Create, Update, Response), SalarioPlus (Create, Update, Response), GrupoMateria (Create, Response)
- [x] 4.2 Agregar schemas para Liquidacion: `LiquidacionResponse`, `LiquidacionKPIs`, `LiquidacionListResponse`, `CalcularLiquidacionRequest`, `CerrarLiquidacionRequest`
- [x] 4.3 Agregar schemas para Factura: `FacturaCreate`, `FacturaResponse`, `FacturaUpdate`
- [x] 4.4 Validar `periodo` con regex `^\d{4}-(0[1-9]|1[0-2])$` en los schemas que lo usan
- [x] 4.5 Todos los schemas con `model_config = ConfigDict(from_attributes=True, extra='forbid')` (response) o `ConfigDict(extra='forbid')` (request)

## 5. Repositorios

- [x] 5.1 Crear `backend/app/repositories/salario_repository.py` con queries para SalarioBase (get_by_rol, create/upsert, list_all, soft_delete), SalarioPlus (get_by_grupo_rol, create/upsert, list_all, soft_delete), GrupoMateria (get_by_grupo, create, delete, list_all)
- [x] 5.2 Crear `backend/app/repositories/liquidacion_repository.py` con queries: get_by_cohorte_periodo, upsert (bulk), close_by_cohorte_periodo, get_history, get_by_usuario_periodo, count_by_estado
- [x] 5.3 Crear `backend/app/repositories/factura_repository.py` con queries: create, get_by_id, list_all (con filtros), soft_delete, update_estado
- [x] 5.4 Todos los repositorios filtran por `tenant_id` automáticamente (patrón multi-tenant)

## 6. Servicio de Cálculo de Liquidación

- [x] 6.1 Crear `backend/app/services/liquidacion_service.py` con método `calcular_liquidacion(cohorte_id, periodo, tenant_id)` que implementa la fórmula RN-34
- [x] 6.2 Implementar resolución de vigencia temporal para SalarioBase y SalarioPlus: `vig_desde <= mes_start AND (vig_hasta IS NULL OR vig_hasta >= mes_end)`
- [x] 6.3 Implementar resolución de GrupoMateria para cada comisión y acumulación por grupo (RN-33)
- [x] 6.4 Manejar multi-rol: si un docente tiene asignaciones con distintos roles, crear una Liquidacion por rol
- [x] 6.5 Detectar `es_nexo` (rol=NEXO) y `excluido_por_factura` (usuario.facturador=True)
- [x] 6.5b Implementar upsert de recálculo: si ya existen Liquidacion Abierta para (cohorte, periodo), actualizar montos; si están Cerradas, lanzar 409 Conflict. Si no existen, crear nuevas. Ver design D13.
- [x] 6.6 Excluir docentes sin SalarioBase vigente del cálculo y reportarlos en la respuesta
- [x] 6.7 Excluir docentes con datos bancarios incompletos (sin CBU ni alias_cbu) y reportarlos (RN-26)
- [x] 6.8 Implementar `cerrar_liquidacion(cohorte_id, periodo, actor_id)` con transición Abierta→Cerrada y auditoría `LIQUIDACION_CERRAR`
- [x] 6.9 Bloquear recalculo y cierre sobre liquidaciones ya Cerradas
- [x] 6.10 Implementar `get_liquidacion_view(cohorte_id, periodo)` con segmentación en 3 grupos y KPIs (RN-36, RN-38)
- [x] 6.11 Implementar `get_historial(cohorte_id)` para listar liquidaciones cerradas de períodos anteriores
- [x] 6.12 Implementar `exportar_liquidacion(cohorte_id, periodo)` generando CSV con filas de liquidación

## 7. Servicio de Facturas

- [x] 7.1 Crear `backend/app/services/factura_service.py` con métodos CRUD: create, get_by_id, list_all, soft_delete
- [x] 7.2 Validar que el `usuario_id` corresponde a un usuario con `facturador=True` al crear una factura
- [x] 7.3 Implementar `abonar_factura(id)` con transición Pendiente→Abonada y timestamp automático en `abonada_at`
- [x] 7.4 Implementar `reabrir_factura(id)` con transición Abonada→Pendiente y `abonada_at` a null
- [x] 7.5 Bloquear transiciones inválidas (abonar ya abonada, reabrir pendiente) con 409 Conflict

## 8. Routers

- [x] 8.1 Crear `backend/app/api/v1/routers/liquidaciones.py` con endpoints
- [x] 8.2 Crear `backend/app/api/v1/routers/facturas.py` con endpoints
- [x] 8.3 Agregar guards `require_permission(...)` en cada endpoint según corresponda (ver design D8)
- [x] 8.4 Registrar ambos routers en `backend/app/main.py`

## 9. Tests unitarios

- [x] 9.1 Tests para `SalarioBaseRepository`: get_by_rol válido, no encontrado, soft_delete excluye, list_all
- [x] 9.2 Tests para `SalarioPlusRepository`: get_by_grupo_rol válido, no encontrado, soft_delete excluye
- [x] 9.3 Tests para `GrupoMateriaRepository`: create, get_by_grupo, delete, duplicate rejection
- [x] 9.4 Tests para `LiquidacionRepository`: upsert, get_by_cohorte_periodo, close_by_cohorte_periodo, get_history
- [x] 9.5 Tests para cálculo de liquidación (RN-34): base+plus normal, sin plus, sin base, multi-rol, NEXO flag, facturante exclusion
- [x] 9.6 Tests para temporal validity: vig_desde dentro/fuera del período, vig_hasta antes/después del período, NULL vig_hasta
- [x] 9.7 Tests para acumulación de plus (RN-33): N comisiones mismo grupo, comisiones en múltiples grupos, sin grupo mapeado
- [x] 9.8 Tests para cierre de liquidación: Abierta→Cerrada exitoso, recalculo bloqueado en Cerrada, cierre duplicado rechazado
- [x] 9.9 Tests para auditoría: LIQUIDACION_CERRAR se registra correctamente con filas_afectadas
- [x] 9.10 Tests para segmentación y KPIs: general+NEXO+facturante, solo general, KPIs correctos
- [x] 9.11 Tests para Factura: create exitoso, create con no-facturante rechazado, abonar→abonada, reabrir→pendiente, transición inválida rechazada
- [x] 9.12 Tests para exportación CSV: estructura esperada, filas correctas, encoding UTF-8

## 10. Tests de integración (API)

- [x] 10.1 Test GET /api/liquidaciones con filtros (cohorte, periodo, docente)
- [x] 10.2 Test POST /api/liquidaciones/calcular — cálculo exitoso, primer cálculo y recálculo
- [x] 10.3 Test POST /api/liquidaciones/{cohorte}/{periodo}/cerrar — cierre exitoso y rechazo en Cerrada
- [x] 10.4 Test GET /api/liquidaciones/historial — solo liquidaciones Cerradas
- [x] 10.5 Test GET /api/liquidaciones/exportar — descarga exitosa
- [x] 10.6 Test CRUD salarios base (GET, POST, PUT, DELETE) con verificación de guards 403
- [x] 10.7 Test CRUD salarios plus (GET, POST, PUT, DELETE) con rechazo de duplicado 409
- [x] 10.8 Test CRUD grupo-materia (GET, POST, DELETE) con rechazo de duplicado 409
- [x] 10.9 Test GET/POST /api/facturas — creación exitosa y rechazo no-facturante
- [x] 10.10 Test PUT /api/facturas/{id}/abonar y /reabrir con transiciones válidas e inválidas
- [x] 10.11 Test DELETE /api/facturas/{id} — soft delete
- [x] 10.12 Test RBAC: usuario sin permisos `liquidaciones:*` recibe 403 en todos los endpoints
- [x] 10.13 Test multi-tenancy: datos de tenant A no visibles desde tenant B en todos los endpoints
