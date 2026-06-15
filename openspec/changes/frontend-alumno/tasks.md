# Tasks: Frontend del Alumno

## 1. Backend — Endpoint estado-académico

- [ ] 1.1 Crear `backend/app/api/v1/routers/alumnos.py` con router prefix `/api/v1/alumnos`
- [ ] 1.2 Implementar `GET /estado-academico` con permiso `estado_academico:ver`
- [ ] 1.3 Crear `backend/app/services/alumno_service.py` con lógica de progreso por materia
- [ ] 1.4 Crear schema `EstadoAcademicoResponse` en `backend/app/schemas/alumno.py`
- [ ] 1.5 Registrar router en `backend/app/api/v1/__init__.py`
- [ ] 1.6 Copiar archivos al container + reiniciar API

## 2. Frontend — Tipos y Servicios

- [ ] 2.1 Crear `features/alumno/types/alumno.types.ts`
- [ ] 2.2 Crear `features/alumno/services/alumno.service.ts`

## 3. Frontend — Hooks

- [ ] 3.1 Crear `features/alumno/hooks/useAlumno.ts` con queries y mutations

## 4. Frontend — Páginas

- [ ] 4.1 Crear `AlumnoDashboardPage.tsx` — resumen con cards
- [ ] 4.2 Crear `EstadoAcademicoPage.tsx` — tabla de materias con progreso
- [ ] 4.3 Crear `MisAvisosPage.tsx` — listado + confirmación de avisos
- [ ] 4.4 Crear `MisColoquiosPage.tsx` — coloquios disponibles + mis reservas

## 5. Frontend — Integración

- [ ] 5.1 Agregar rutas en `App.tsx` con `RequirePermission`
- [ ] 5.2 Agregar grupo "Alumno" en `nav.ts` (NAV_ITEMS)
- [ ] 5.3 Extender `DashboardPage.tsx` con sección específica ALUMNO

## 6. Build & Verify

- [ ] 6.1 Rebuild frontend + backend containers
- [ ] 6.2 Verificar que el ALUMNO ve el nuevo menú y páginas
