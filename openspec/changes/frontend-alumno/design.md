# Design: Frontend del Alumno

## Architecture

```
features/alumno/
├── types/alumno.types.ts
├── services/alumno.service.ts
├── hooks/useAlumno.ts
├── pages/
│   ├── AlumnoDashboardPage.tsx
│   ├── EstadoAcademicoPage.tsx
│   ├── MisAvisosPage.tsx
│   └── MisColoquiosPage.tsx
```

### Data Flow
```
Page → Hook (TanStack Query) → Service (axios) → Backend API
```

## Backend: Nuevo Endpoint

### `GET /api/v1/alumnos/estado-academico`

**Router**: `backend/app/api/v1/routers/alumnos.py` (nuevo)
**Permiso**: `estado_academico:ver`
**Service**: `AlumnoService` en `backend/app/services/alumno_service.py` (nuevo)

**Response**:
```json
{
  "materias": [{
    "materia_id": "uuid",
    "materia_nombre": "Matemática I",
    "carrera_nombre": "Ing. Sistemas",
    "cohorte_nombre": "2025-C1",
    "actividades_aprobadas": 8,
    "actividades_totales": 10,
    "porcentaje_aprobacion": 80,
    "estado": "Regular"
  }],
  "resumen": {
    "materias_totales": 3,
    "materias_regulares": 2,
    "materias_en_riesgo": 1
  }
}
```

**Lógica**: El endpoint consulta las asignaciones del alumno (`Asignacion` con rol ALUMNO), resuelve las materias asignadas, y para cada materia calcula el progreso usando las calificaciones existentes y el umbral configurado.

## Frontend Pages

### 1. AlumnoDashboardPage (`/alumno`)
- Cards de resumen: materias totales, regulares, en riesgo
- Lista de avisos pendientes (últimos 3)
- Próximos coloquios disponibles
- Usa `useAuth()` para obtener datos del usuario

### 2. EstadoAcademicoPage (`/alumno/estado`)
- Tabla con columnas: Materia, Carrera, Cohorte, % Aprobación, Estado
- Hook: `useEstadoAcademico()` → `GET /api/v1/alumnos/estado-academico`
- Loading state con Spinner, empty state con mensaje

### 3. MisAvisosPage (`/alumno/avisos`)
- Tabla de avisos visibles con columnas: Título, Fecha, Confirmado
- Botón "Confirmar lectura" en cada aviso no confirmado
- Hook: `useAvisos()` reusando `GET /api/avisos` + `POST /api/avisos/{id}/ack`

### 4. MisColoquiosPage (`/alumno/coloquios`)
- Dos tabs/secciones: "Disponibles" y "Mis Reservas"
- **Disponibles**: convocatorias abiertas con botón "Reservar"
- **Mis Reservas**: tabla con reservas activas + botón "Cancelar"
- Hooks: `useColoquiosDisponibles()`, `useMisReservas()`, `useReservar()`, `useCancelarReserva()`

## Nav Items

```ts
{
  label: 'Alumno',
  path: '/alumno',
  permission: null,
  children: [
    { label: 'Mi Estado', path: '/alumno/estado', permission: 'estado_academico:ver' },
    { label: 'Mis Avisos', path: '/alumno/avisos', permission: 'aviso:confirmar' },
    { label: 'Coloquios', path: '/alumno/coloquios', permission: 'coloquios:reservar' },
  ],
}
```

## Routes (App.tsx)

```tsx
<Route path="/alumno" element={<RequirePermission requiredPermission="estado_academico:ver"><AlumnoDashboardPage /></RequirePermission>} />
<Route path="/alumno/estado" element={<RequirePermission requiredPermission="estado_academico:ver"><EstadoAcademicoPage /></RequirePermission>} />
<Route path="/alumno/avisos" element={<RequirePermission requiredPermission="aviso:confirmar"><MisAvisosPage /></RequirePermission>} />
<Route path="/alumno/coloquios" element={<RequirePermission requiredPermission="coloquios:reservar"><MisColoquiosPage /></RequirePermission>} />
```

## Dashboard Enhancement

El `DashboardPage` actual detecta `isAdmin`. Se agrega `isAlumno` con cards específicas:
- Estado general (regular/en riesgo)
- Próximo coloquio
- Avisos sin confirmar (badge con count)
