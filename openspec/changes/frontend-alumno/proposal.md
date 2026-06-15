# Proposal: Frontend del Alumno

## What

Implementar la interfaz completa del rol ALUMNO para que pueda consultar su estado académico, ver y confirmar avisos, y reservar/cancelar turnos de coloquio desde el frontend.

## Why

El rol ALUMNO existe en el backend con sus permisos (`estado_academico:ver`, `aviso:confirmar`, `coloquios:reservar`) y endpoints funcionales, pero el frontend nunca fue implementado. Actualmente un ALUMNO solo ve el Dashboard vacío.

## What Changes

### Backend (1 nuevo endpoint)
- `GET /api/v1/alumnos/estado-academico` — Devuelve materias, calificaciones y progreso del alumno autenticado

### Frontend (nuevo módulo `features/alumno/`)
- **Dashboard Alumno**: resumen con materias, próximos coloquios, avisos pendientes
- **Mi Estado Académico**: tabla de materias con calificaciones, porcentaje de aprobación y estado
- **Mis Avisos**: listado de avisos visibles + confirmación de lectura
- **Coloquios**: listado de convocatorias disponibles + reserva de turno
- **Mis Reservas**: listado de reservas activas + cancelación

### Modificaciones
- `App.tsx`: rutas nuevas con `RequirePermission`
- `nav.ts`: nuevo grupo "Alumno" en `NAV_ITEMS`
- `DashboardPage.tsx`: contenido específico para ALUMNO

## Impact

- **Governance**: MEDIUM (lógica de dominio, sin tocar auth/RBAC)
- **Roles afectados**: solo ALUMNO
- **No rompe nada existente**: rutas y nav items nuevos, sin modificar comportamiento de otros roles
