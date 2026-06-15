## 1. Setup y Estructura del Feature Module

- [x] 1.1 Crear estructura de directorios `features/academico/` con subdirectorios: `pages/`, `components/`, `hooks/`, `services/`, `types/`
- [x] 1.2 Crear `features/academico/types/calificaciones.types.ts` con interfaces para Calificacion, ActividadDetectada, PreviewResponse, UmbralConfig
- [x] 1.3 Crear `features/academico/types/analisis.types.ts` con interfaces para AlumnoAtrasado, RankingItem, NotaFinal, MetricaReporte, EntradaMonitor
- [x] 1.4 Crear `features/academico/types/comunicaciones.types.ts` con interfaces para ComunicacionPreview, EstadoComunicacion, LoteEnvio
- [x] 1.5 Crear `features/academico/services/calificaciones.service.ts` con funciones: `uploadCalificaciones(formData)`, `getPreview(materiaId)`, `confirmarImportacion(materiaId, actividades)`, `getUmbral(materiaId)`, `setUmbral(materiaId, pct)`
- [x] 1.6 Crear `features/academico/services/analisis.service.ts` con funciones: `getAtrasados(materiaId, filtros)`, `getRanking(materiaId)`, `getNotasFinales(materiaId)`, `getReportesRapidos(materiaId)`, `getMonitores(filtros)`, `uploadReporteFinalizacion(formData)`, `getEntregasSinCorregir(materiaId)`, `exportEntregasSinCorregir(materiaId)`
- [x] 1.7 Crear `features/academico/services/comunicaciones.service.ts` con funciones: `getPreview(alumnosIds)`, `enviarComunicacion(payload)`, `getEstadoComunicaciones(loteId)`, `cancelarComunicacion(comunicacionId)`

## 2. Componentes Compartidos (shared/components/ui/)

- [x] 2.1 Crear `shared/components/ui/DataTable.tsx` — tabla genérica con columnas tipadas, sorting por columna, paginación opcional, y slot para acciones/filtros
- [x] 2.2 Crear `shared/components/ui/FileUpload.tsx` — componente drag-and-drop con validación de tipo y tamaño, barra de progreso vía Axios `onUploadProgress`
- [x] 2.3 Crear `shared/components/ui/StatusBadge.tsx` — badge coloreado según estado (Pendiente=amarillo, Enviando=azul, Enviado=verde, Error=rojo, Cancelado=gris)
- [x] 2.4 Crear `shared/components/ui/Select.tsx` — componente select estilizado con label y error (análogo a Input.tsx)

## 3. Selector de Materia (Componente Transversal)

- [x] 3.1 Crear `features/academico/components/MateriaSelector.tsx` — dropdown que consulta materias asignadas al profesor (endpoint de C-08) y expone la materia seleccionada
- [x] 3.2 Crear `features/academico/hooks/useMateriaSeleccionada.ts` — hook que mantiene el estado de la materia seleccionada y lo persiste en la URL (search param `?materiaId=`)

## 4. Página: Importación de Calificaciones

- [x] 4.1 Crear `features/academico/hooks/useCalificaciones.ts` — hook con `useMutation` para upload de archivo, `useQuery` para preview, y `useMutation` para confirmar importación
- [x] 4.2 Crear `features/academico/components/ActividadesPreview.tsx` — tabla que muestra actividades detectadas con checkboxes de selección usando DataTable
- [x] 4.3 Crear `features/academico/pages/ImportarCalificacionesPage.tsx` — página completa con: MateriaSelector, FileUpload, ActividadesPreview, botón confirmar. Muestra progress durante upload. Sin actividades seleccionadas el botón está disabled
- [x] 4.4 Manejar estados: loading (spinner durante upload), empty (primer acceso), error (archivo inválido, tamaño excedido), success (datos importados)

## 5. Página: Configuración de Umbral

- [x] 5.1 Crear `features/academico/hooks/useUmbral.ts` — hook con `useQuery` para obtener umbral actual y `useMutation` para guardarlo
- [x] 5.2 Crear `features/academico/pages/ConfigurarUmbralPage.tsx` — formulario con Input numérico (0-100), valor por defecto 60%, botón guardar. Muestra aviso si la materia ya tiene calificaciones importadas

## 6. Página: Vista de Atrasados

- [x] 6.1 Crear `features/academico/hooks/useAtrasados.ts` — hook con `useQuery` para obtener atrasados según filtros (materiaId, minFaltantes, maxPorcentaje)
- [x] 6.2 Crear `features/academico/components/AtrasadosTable.tsx` — tabla con columnas: nombre, estado actividades, faltantes, % aprobación, checkbox de selección. Usa DataTable + StatusBadge
- [x] 6.3 Crear `features/academico/pages/VistaAtrasadosPage.tsx` — página con MateriaSelector, filtros (min faltantes, max %), AtrasadosTable, botón "Comunicar" (navega a /comunicaciones con seleccionados), botón "Seleccionar todos"
- [x] 6.4 Manejar estados: loading, empty (sin atrasados), empty (sin datos importados — mensaje informativo con link a importar)

## 7. Página: Ranking

- [x] 7.1 Crear `features/academico/hooks/useRanking.ts` — hook con `useQuery` para obtener ranking
- [x] 7.2 Crear `features/academico/pages/RankingPage.tsx` — página con MateriaSelector, tabla ordenada desc por aprobadas, columnas: nombre, X/Y aprobadas, %. Manejar empty (sin datos, sin aprobadas)

## 8. Página: Notas Finales

- [x] 8.1 Crear `features/academico/hooks/useNotasFinales.ts` — hook con `useQuery` para obtener notas finales
- [x] 8.2 Crear `features/academico/pages/NotasFinalesPage.tsx` — página con MateriaSelector, tabla de notas finales por alumno, botón exportar (.xlsx). Export deshabilitado sin datos

## 9. Página: Reportes Rápidos

- [x] 9.1 Crear `features/academico/hooks/useReportes.ts` — hook con `useQuery` para obtener métricas de reportes rápidos
- [x] 9.2 Crear `features/academico/components/MetricasCards.tsx` — grid de cards con métricas: total alumnos, tasa aprobación, promedio, atrasados. Con barras de progreso por actividad
- [x] 9.3 Crear `features/academico/pages/ReportesPage.tsx` — página con MateriaSelector, MetricasCards, enlaces a vista de atrasados y ranking. Estado empty sin datos

## 10. Página: Detección de Entregas sin Corregir

- [x] 10.1 Crear `features/academico/hooks/useEntregasSinCorregir.ts` — hook con `useMutation` para upload de reporte de finalización, `useQuery` para tabla de entregas sin corregir, y `useMutation` para exportar
- [x] 10.2 Crear `features/academico/pages/DeteccionEntregasPage.tsx` — página con MateriaSelector, FileUpload (reporte finalización), tabla de entregas sin corregir (alumno, actividad, estado), botón exportar. Aviso si no hay calificaciones previas

## 11. Flujo de Comunicación a Atrasados

- [x] 11.1 Crear `features/academico/hooks/useComunicaciones.ts` — hook con `useQuery` para preview, `useMutation` para enviar, y `useQuery` con `refetchInterval: 5000` para tracking de estados (polling se detiene cuando todos en estado final)
- [x] 11.2 Crear `features/academico/components/ComunicacionPreview.tsx` — lista de mensajes previsualizados por alumno con asunto y cuerpo sustituidos
- [x] 11.3 Crear `features/academico/components/ComunicacionTracker.tsx` — tabla de tracking con columnas: destinatario, estado (StatusBadge), fecha. Muestra resumen con contadores por estado al finalizar
- [x] 11.4 Crear `features/academico/pages/ComunicacionesPage.tsx` — página con dos vistas: (a) preview con botones Confirmar/Cancelar, (b) tracking post-envío con polling. Si no vienen alumnos seleccionados de atrasados, muestra mensaje para volver

## 12. Páginas: Monitores de Seguimiento

- [x] 12.1 Crear `features/academico/hooks/useMonitores.ts` — hook con `useQuery` para obtener datos del monitor según filtros
- [x] 12.2 Crear `features/academico/components/FiltrosMonitor.tsx` — barra de filtros: alumno (búsqueda texto), correo, comisión, regional, actividad, mínimo actividades cumplidas, rango de fechas (solo para COORDINADOR/ADMIN)
- [x] 12.3 Crear `features/academico/pages/MonitoresSeguimientoPage.tsx` — página con MateriaSelector (opcional — el monitor puede ser global para el profesor), FiltrosMonitor, DataTable con datos del monitor, botón Exportar. El filtro de fechas se muestra condicionalmente según rol

## 13. Integración de Rutas en App.tsx

- [x] 13.1 Agregar imports de todas las páginas del feature académico en App.tsx
- [x] 13.2 Agregar rutas bajo `<Route element={<AppLayout />}>` envueltas en `<RequirePermission>`:
  - `/academico/importar` → ImportarCalificacionesPage (`calificaciones:importar`)
  - `/academico/umbral` → ConfigurarUmbralPage (`calificaciones:importar`)
  - `/academico/atrasados` → VistaAtrasadosPage (`atrasados:ver`)
  - `/academico/ranking` → RankingPage (`atrasados:ver`)
  - `/academico/notas-finales` → NotasFinalesPage (`atrasados:ver`)
  - `/academico/reportes` → ReportesPage (`atrasados:ver`)
  - `/academico/entregas` → DeteccionEntregasPage (`atrasados:ver`)
  - `/academico/comunicaciones` → ComunicacionesPage (`comunicacion:enviar`)
  - `/academico/monitores` → MonitoresSeguimientoPage (`atrasados:ver`)
- [x] 13.3 Agregar entradas en el Sidebar para el menú "Académico" con sub-items según permisos

## 14. Tests

- [x] 14.1 Test de FileUpload: renderizado, validación de tipos, validación de tamaño, callback de progreso
- [x] 14.2 Test de DataTable: renderizado con datos, ordenamiento, paginación, fila vacía
- [x] 14.3 Test de StatusBadge: renderizado de cada variante de estado con color correcto
- [x] 14.4 Test de MateriaSelector: carga de materias, selección, persistencia en URL
- [x] 14.5 Test de ImportarCalificacionesPage: flujo completo (upload → preview → selección → confirmación) con mocks de API
- [x] 14.6 Test de VistaAtrasadosPage: renderizado con datos, filtros, selección múltiple, navegación a comunicaciones
- [x] 14.7 Test de ComunicacionesPage: preview, confirmación de envío, tracking con polling (mock de TanStack Query)
- [x] 14.8 Test de guards: rutas redirigen a 403 si falta permiso (usar RequirePermission mockeado)

## 15. Polish y Edge Cases

- [x] 15.1 Agregar loading skeletons para todas las tablas mientras los datos se cargan (usar Spinner o skeleton cards)
- [x] 15.2 Agregar mensajes de error con retry para queries fallidas (error boundary liviano a nivel página)
- [x] 15.3 Agregar empty states informativos para cada página con call-to-action (ej: "Todavía no importaste calificaciones. Empezá por acá.")
- [x] 15.4 Validar que el botón Exportar esté disabled cuando no hay datos en la tabla
- [x] 15.5 Verificar que el polling de comunicaciones se detenga efectivamente cuando todas están en estado final (useEffect cleanup)
