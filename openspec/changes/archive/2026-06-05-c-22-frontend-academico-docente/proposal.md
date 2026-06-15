## Why

El PROFESOR necesita una interfaz completa para gestionar su comisión académica: importar calificaciones desde el LMS, configurar umbrales de aprobación, visualizar alumnos atrasados, rankings, notas finales, reportes rápidos, detectar entregas sin corregir y comunicarse con alumnos atrasados con tracking de estado en tiempo real. Los endpoints de backend para estas capacidades (C-10 calificaciones, C-11 análisis, C-12 comunicaciones) ya están implementados. Este change provee la capa de presentación que los consume.

## What Changes

- Nuevo módulo feature-based `features/academico/` con estructura completa (pages, components, hooks, services, types)
- Página de importación de calificaciones con preview de actividades detectadas y selección de cuáles incluir
- Página de configuración de umbral de aprobación por materia
- Página de visualización de alumnos atrasados con tabla filtrable y acciones de comunicación
- Página de ranking de actividades aprobadas por alumno
- Página de notas finales agrupadas por alumno con opción de exportación
- Página de reportes rápidos con métricas clave de la materia
- Página de detección de entregas sin corregir con importación de reporte de finalización y exportación
- Flujo de comunicación a atrasados: preview de mensaje personalizado, envío masivo a cola, tracking de estado en tiempo real (polling)
- Páginas de monitores de seguimiento: vista tutor/profesor y vista coordinación/admin
- Integración con TanStack Query para todo el fetching de datos con invalidación de caché
- Guards de permisos finos (`calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`, etc.)
- Rutas nuevas bajo `/academico/*` dentro del `AppLayout` protegido

## Capabilities

### New Capabilities

- `importacion-calificaciones`: Subida de archivo con preview de actividades y selección de cuáles incluir en el análisis. Consume C-10.
- `configuracion-umbral`: Configuración del porcentaje de aprobación por materia con valor por defecto 60%.
- `vista-atrasados`: Tabla de alumnos con actividades faltantes o nota inferior al umbral, con filtros y acciones de comunicación.
- `ranking-actividades`: Tabla ordenada por cantidad de actividades aprobadas por alumno.
- `notas-finales`: Vista agrupada de notas finales calculadas por alumno con exportación.
- `reportes-rapidos`: Vista consolidada de métricas clave de la materia (actividades, aprobaciones, tendencias).
- `deteccion-entregas-sin-corregir`: Importación de reporte de finalización del LMS + cruce con calificaciones + exportación del listado.
- `comunicacion-atrasados`: Preview de mensaje personalizado, envío a cola, y tracking de estado en tiempo real por polling. Consume C-12.
- `monitores-seguimiento`: Vista filtrable del estado de actividades por alumno (tutor/profesor) y vista extendida con rango de fechas (coordinación/admin). Consume C-11.

### Modified Capabilities

Ninguna — este change introduce capacidades nuevas sin modificar specs existentes.

## Impact

- **Código afectado**: nuevo feature `frontend/src/features/academico/` con ~15 archivos (pages, components, hooks, services, types)
- **Rutas**: nuevas rutas bajo `AppLayout` en `App.tsx` para `/academico/*`
- **Dependencias backend**: endpoints de C-10 (`/api/calificaciones/*`), C-11 (`/api/analisis/*`), C-12 (`/api/comunicaciones/*`)
- **Dependencias frontend**: C-21 (shell, auth, layout, guards, UI components, API client)
- **UI components reusables**: Button, Input, Card, Alert, Spinner (ya existentes en `shared/components/ui/`), más nuevos componentes de tabla, file upload, modal
- **Permisos requeridos**: `calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar` (definidos en C-04 rbac)
- **Sin impacto en infraestructura**: todo es frontend puro; no requiere migraciones ni cambios de deploy
