## Context

El backend de activia-trace ya expone los endpoints para calificaciones (C-10), análisis y atrasados (C-11) y comunicaciones con cola y worker (C-12). El shell frontend (C-21) ya provee autenticación, guards de permisos, layout con sidebar/topbar, cliente HTTP con refresh automático, y componentes UI base (Button, Input, Card, Alert, Spinner). Este change construye el feature module `academico/` que consume esos endpoints y expone la interfaz completa para el PROFESOR.

## Goals / Non-Goals

**Goals:**
- Feature module `features/academico/` con estructura canónica (pages, components, hooks, services, types)
- 8 páginas que cubren el flujo completo FL-02 y FL-04 del profesor
- TanStack Query para todo fetching de datos con invalidación de caché
- Guards de permisos por ruta: `calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`
- Tracking de estado de comunicaciones en tiempo real vía polling
- Componentes reusables nuevos: DataTable, FileUpload, StatusBadge (en shared/components si son genéricos)

**Non-Goals:**
- No modifica el backend ni la API existente
- No incluye la vista de coordinación/admin (eso es C-23)
- No implementa WebSockets — el tracking usa polling
- No incluye i18n (todo en español rioplatense)
- No modifica la estructura del layout existente

## Decisions

### D1: Feature module `features/academico/` con sub-módulos por dominio

Se agrupan las páginas en un solo feature `academico/` porque comparten servicios y tipos (calificaciones, análisis, comunicaciones son parte del mismo flujo FL-02). Separar en features más chicos (`features/calificaciones/`, `features/atrasados/`, `features/comunicaciones/`) crearía acoplamiento entre features y duplicación de tipos.

Alternativa considerada: features independientes por backend domain. Descartada porque el flujo FL-02 es cohesivo — el profesor importa calificaciones, configura umbral, ve atrasados, y envía comunicaciones en una misma sesión de trabajo. Separarlos rompe la experiencia.

### D2: TanStack Query para todo el server state

Cada página tiene su hook `useCalificaciones`, `useAtrasados`, etc. que usa `useQuery`/`useMutation` de TanStack Query. Los query keys siguen la convención `['domain', id, ...filtros]`. Las mutaciones (`importarCalificaciones`, `enviarComunicacion`) invalidan queries relacionadas al completar.

Alternativa considerada: estado local con useEffect + fetch. Descartada porque TanStack Query ya es el estándar del proyecto y maneja caching, refetch, estados de loading/error, e invalidación automática.

### D3: Polling para tracking de comunicaciones

El estado de cada comunicación se refresca con `refetchInterval: 5000` en `useQuery` mientras haya comunicaciones en estado Pendiente/Enviando. Cuando todas llegan a estado final (Enviado/Error/Cancelado), el polling se detiene.

Alternativa considerada: Server-Sent Events o WebSockets. Descartada por simplicidad — polling cada 5 segundos es suficiente para el caso de uso y no requiere infraestructura adicional en backend.

### D4: Componentes genéricos nuevos en `shared/components/`

`DataTable` (tabla con sorting y paginación), `FileUpload` (drag-and-drop con preview), `StatusBadge` (badge de estado coloreado) son reusables y vivirán en `shared/components/`. Componentes específicos del dominio académico (ej. `AtrasadosTable`, `ComunicacionPreview`) viven en `features/academico/components/`.

### D5: Selector de materia como requisito previo

Varias páginas del feature requieren seleccionar una materia/comisión antes de operar. Se implementa un `MateriaSelector` como componente shared dentro del feature que consulta las materias asignadas al profesor (vía endpoint de C-07/C-08). El estado de la materia seleccionada se comparte vía contexto del feature o URL param.

### D6: Estructura de rutas bajo `/academico/`

```
/academico/importar          — ImportarCalificaciones (calificaciones:importar)
/academico/umbral            — ConfigurarUmbral (calificaciones:importar)
/academico/atrasados         — VistaAtrasados (atrasados:ver)
/academico/ranking           — Ranking (atrasados:ver)
/academico/notas-finales     — NotasFinales (atrasados:ver)
/academico/reportes          — Reportes (atrasados:ver)
/academico/entregas          — DeteccionEntregas (atrasados:ver)
/academico/comunicaciones    — ComunicacionesPreview (comunicacion:enviar)
/academico/monitores         — MonitoresSeguimiento (atrasados:ver)
```

Cada ruta se envuelve en `ProtectedRoute` > `AppLayout` > `RequirePermission`.

## Risks / Trade-offs

- **[R1] Dependencia de endpoints de C-10/C-11/C-12 sin tests E2E**: si la API cambia la forma de los datos, el frontend rompe. → Mitigación: tipado estricto de respuestas en `types/` con Zod runtime validation opcional en desarrollo.
- **[R2] Polling puede saturar el servidor si muchos profesores monitorean simultáneamente**: 5s por request por profesor es aceptable, pero a escala puede ser un problema. → Mitigación: el polling solo se activa mientras hay comunicaciones pendientes (no es perpetuo). Migrar a SSE/WS si escala.
- **[R3] File upload de archivos grandes**: el LMS puede exportar planillas de 10MB+. → Mitigación: mostrar progress bar durante el upload vía Axios `onUploadProgress`. Validar tamaño máximo en frontend (20MB).
- **[R4] Componentes nuevos en shared pueden crear deuda si no son suficientemente genéricos**: DataTable, FileUpload nacen para académico pero deben ser reusables para C-23/C-24. → Mitigación: diseñarlos con props genéricas desde el inicio (columnas tipadas, callbacks para renderizado custom).

## Open Questions

- **Formato exacto de la respuesta del endpoint de preview de calificaciones** (C-10): ¿viene como array de actividades con columnas de alumnos o como matriz? Se asume el formato documentado en KB-04 para la implementación inicial.
- **Endpoint de materias asignadas al profesor**: ¿es `/api/equipos/mis-materias` de C-08 o hay un endpoint más específico para obtener solo materias? Se usa el que exponga C-08; si no existe, se agrega un helper en `academico.service.ts`.
