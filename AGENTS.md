# activia-trace — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/`, `docs/ARQUITECTURA.md` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

**activia-trace** es una plataforma de gestión académica y trazabilidad multi-tenant que opera como capa de orquestación sobre Moodle: consolida calificaciones, detecta atrasos, gestiona comunicación saliente con aprobación, equipos docentes, encuentros, coloquios, liquidaciones de honorarios y auditoría completa. Cada institución es un tenant aislado; el nombre del producto es *trace* — todo audita.

---

## Stack Tecnológico

Detalle completo en [docs/ARQUITECTURA.md §2](docs/ARQUITECTURA.md). Resumen funcional en [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md).

### Backend
| Componente | Tecnología | Notas |
|------------|-----------|-------|
| Lenguaje | **Python 3.13** | snake_case en todo |
| Framework | **FastAPI** | API REST async |
| ORM | **SQLAlchemy 2.0** (async) | Queries SOLO en repositories |
| Migraciones | **Alembic** | Una migración por cambio de schema |
| Base de datos | **PostgreSQL** | JSONB para criterios/scores configurables |
| Validación | **Pydantic v2** | DTOs request/response; `extra='forbid'` |
| Auth | **JWT** (access corto + refresh rotation) + **Argon2id** | hashing de passwords |
| Cifrado en reposo | **AES-256** | PII sensible (CBU, DNI) y secretos |
| Background jobs | **Worker async** | cola de comunicaciones (Pend→Send→OK/Fail / Pend→Canc) |
| Integraciones | **N8N** + **Moodle Web Services** | cliente dedicado `moodle_ws.py` |
| Testing | **pytest** + coverage | ≥80% líneas, ≥90% reglas de negocio |

### Frontend
| Componente | Tecnología | Notas |
|------------|-----------|-------|
| Framework | **React 18** + **TypeScript** | Sin `any`, sin class components |
| Bundler | **Vite** | HMR en dev |
| Server state | **TanStack Query** | Todo fetch pasa por hooks de `services/` |
| Forms | **React Hook Form + Zod** | Validación tipada |
| Estilos | **Tailwind CSS** | Sin CSS modules, sin inline (salvo valores dinámicos) |
| HTTP | **Axios** | Cliente centralizado en `@/shared/services/api` |
| Estructura | **Feature-based modules** | `features/{name}/{components,hooks,services,types,pages}` |

### Infraestructura
| Componente | Tecnología |
|------------|-----------|
| Contenedores | **Docker** + docker-compose (local y prod) |
| Deploy | **Easypanel** |
| Observabilidad | Logs estructurados JSON + **OpenTelemetry** |

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/` (agnóstica de tecnología). El detalle técnico vive en `docs/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Sistema, integraciones, propiedades de seguridad |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos, matriz de capacidades, impersonación |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, migraciones |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-XX) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Funcionalidades por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E (importación, mensajería, auth) |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones y estructura de producto |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones cerradas y supuestos base |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |
| [11_historias_de_usuario.md](knowledge-base/11_historias_de_usuario.md) | Historias (Connextra) + criterios de aceptación |
| [docs/PRD.md](docs/PRD.md) | Requerimientos de producto y RNF |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Stack, Clean Architecture, estructura de directorios, seguridad |

> ⚠️ **Roles del dominio**: ALUMNO · TUTOR · PROFESOR · COORDINADOR · NEXO · ADMIN · FINANZAS. Leé `03_actores_y_roles.md` para internalizar el modelo de permisos ANTES de cualquier implementación.

> ℹ️ **Preguntas ALTA resueltas** (2026-06-08): PA-01 (catálogo único Materia), PA-07 (cohortes por carrera), PA-22 (Plus configurable por tenant vía `Materia.grupo_plus`), PA-23 (acumulación lineal por comisión), PA-25 (NEXO = enlace administrativo-pedagógico). Ver tabla de decisiones cerradas en [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md). Las preguntas de prioridad MEDIA y BAJA siguen abiertas — revisar antes de implementar módulos afectados.

---

## Skills Disponibles

Cargá la skill correspondiente al contexto **ANTES** de escribir código. Aplicá todos sus patrones.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI / SQLAlchemy / migraciones / modelos | `fastapi-templates`, `postgresql-table-design`, `python-testing-patterns`, `test-driven-development` |
| **Backend Aux** | Servicios, integraciones, seguridad, performance | `api-security-best-practices`, `postgresql-optimization`, `systematic-debugging` |
| **Frontend** | React / TanStack / Tailwind / E2E | `typescript-advanced-types`, `tailwind-design-system`, `playwright-best-practices` |
| **DevOps** | Contenedores / build | `multi-stage-dockerfile` |
| **Transversal** | Calidad / revisión | `code-review-excellence`, `systematic-debugging`, `judgment-day` |
| **Orquestación** | OPSX / docs | `openspec-explore`, `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-design`, `openspec-spec`, `openspec-tasks`, `openspec-verify`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `find-skill` |

> **Gap conocido**: no hay skill de buenas prácticas React instalada (`vercel-react-best-practices` recomendada pero NO instalada por decisión del usuario). El stack queda cubierto ~100% por las skills preinstaladas.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 24 changes (`C-01`…`C-24`) en 6 fases, organizados con 11 gates de paralelismo y un plan óptimo de 3 agentes (Backend Core / Backend Aux / Frontend).
- **Camino crítico** (10 changes, mínimo irreducible): `C-01 → C-02 → C-03 → C-04 → C-06 → C-07 → C-09 → C-10 → C-11 → C-12`. Es el flujo de mayor valor: importar → analizar → comunicar, en producción multi-tenant.
- **Primer fork** (GATE 4, tras `C-04 rbac`): seguridad lista → arrancan en paralelo `C-05 audit-log`, `C-06 estructura-academica` y `C-21 frontend-shell-y-auth`.

### Progreso actual

| Change | Estado | Archivado |
|--------|--------|-----------|
| C-01 foundation-setup | ✅ Completo | 2026-06-03 |
| C-02 core-models-y-tenancy | ✅ Completo | 2026-06-02 |
| C-03 auth-jwt-2fa | ✅ Completo | 2026-06-02 |
| C-04 rbac-permisos-finos | ✅ Completo | 2026-06-03 |
| C-05 audit-log | ✅ Completo | 2026-06-02 |
| C-06 estructura-academica | ✅ Completo | 2026-06-02 |
| C-07 usuarios-y-asignaciones | ✅ Completo | 2026-06-03 |
| C-08 equipos-docentes | ✅ Completo | 2026-06-03 |
| C-09 padron-ingesta-moodle | ✅ Completo | 2026-06-03 |
| C-10 calificaciones-y-umbral | ✅ Completo | 2026-06-03 |
| C-11 analisis-atrasados-reportes | ✅ Completo | 2026-06-03 |
| C-12 comunicaciones-cola-worker | ✅ Completo | 2026-06-03 |
| C-13 encuentros-y-guardias | ✅ Completo | 2026-06-03 |
| C-14 evaluaciones-y-coloquios | ✅ Completo | 2026-06-03 |
| C-15 avisos-y-acknowledgment | ✅ Completo | 2026-06-03 |
| C-16 tareas-internas | ✅ Completo | 2026-06-03 |
| C-17 programas-y-fechas-academicas | ✅ Completo | 2026-06-03 |
| C-18 liquidaciones-y-honorarios | ✅ Completo | 2026-06-03 |
| C-19 panel-auditoria-metricas | ✅ Completo | 2026-06-03 |
| C-20 perfil-y-mensajeria-interna | ✅ Completo | 2026-06-04 |
| C-21 frontend-shell-y-auth | ✅ Completo | 2026-06-03 |
| C-22 frontend-academico-docente | ✅ Completo | 2026-06-05 |
| C-23 frontend-coordinacion | ✅ Completo | 2026-06-05 |
| C-24 frontend-finanzas-y-admin | ✅ Completo | 2026-06-05 |

**Los 24 changes del roadmap están COMPLETOS y ARCHIVADOS.** Ejecutar tests SIEMPRE desde `backend/` (`pytest -q` desde `active-trace\backend\`).

**Próximo paso**: Si se necesita una nueva funcionalidad, crear un issue nuevo, definir un nuevo change (C-25+) y agregarlo a [CHANGES.md](CHANGES.md). Para cambios existentes que requieran ajustes, usar `/opsx:explore` para diagnosticar y luego `/opsx:propose` con un nombre descriptivo.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), verificá que el change no exista ya, respetá las dependencias y leé los archivos de "Leer antes" correspondientes.

---

## Reglas Duras (no negociables)

Estas reglas son **contrato**. Romperlas es un defecto, no una decisión de estilo. Ante conflicto entre la KB y este archivo, prevalecen las reglas duras.

### Generales
1. **No buildear automático.** Nunca ejecutar build/compile/bundle sin pedido explícito del usuario.
2. **No commitear sin pedido explícito.** `git add`/`commit`/`push` SOLO cuando el usuario lo pide. Si estás en la rama default, ramificá antes.
3. **Conventional Commits sin `Co-Authored-By`.** Formato `tipo(scope): mensaje`. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Scopes: `auth`, `tenancy`, `users`, `alumnos`, `materias`, `comisiones`, `entregas`, `comunicacion`, `equipos`, `encuentros`, `coloquios`, `liquidaciones`, `auditoria`, `moodle`, `padron`, `api`, `ui`. JAMÁS agregar atribución a IA ni `Co-Authored-By`.
4. **Tests sin mocks de DB.** Usar base real o contenedor de test (DB efímera). Mockear la base de datos invalida el test — no prueba nada.
5. **Ejecutar tests SIEMPRE desde `backend/`.** El comando es `pytest -q` desde `active-trace\backend\`. NO ejecutar desde la raíz del repo — el conftest resuelve distinto y da falsos fallos.
6. **Pydantic schemas con `extra='forbid'`.** Todo schema rechaza campos no declarados (`model_config = ConfigDict(extra='forbid')`).
7. **snake_case en Python.** Funciones, variables, columnas de BD, módulos y paquetes.
8. **PascalCase en componentes React.** Nombre del componente y del archivo (`ProductCard.tsx`). Sin `any`, sin class components.

### Seguridad y arquitectura (fundacionales — fallan en code review)
- **Identidad SIEMPRE desde la sesión** (JWT verificado). JAMÁS desde un parámetro de URL, body, header ni cualquier dato de la petición. Esto define quién es el usuario, sus roles y su tenant. Sin excepciones.
- **Multi-tenancy row-level.** `tenant_id` en cada tabla; los repositories filtran por tenant **por defecto**. Un query sin scope de tenant es un bug que falla en code review.
- **RBAC fino `modulo:accion`**, no flags binarios ni superusuario. Cada endpoint declara `require_permission(...)`. **Fail-closed**: sin permiso explícito → 403.
- **Nunca lógica de negocio en Routers.** Nunca acceso directo a DB desde Services (siempre vía Repository). Flujo unidireccional Routers → Services → Repositories → Models.
- **Secretos y PII (CBU, DNI) SIEMPRE AES-256.** Passwords con Argon2id. Nunca texto plano.
- **Soft delete siempre** (auditoría append-only). Nunca hard delete.
- **Identidad por UUID interno.** El legajo es un atributo de negocio, nunca credencial ni selector de sesión.
- **≤500 LOC por archivo backend**, componentes React <200 LOC. Una migración Alembic por cambio de schema.
- **Cobertura mínima**: ≥80% líneas, ≥90% reglas de negocio. **Strict TDD**: test que falla → código mínimo → triangulación → refactor.

---

## Agent Governance — Autonomía por dominio

La autonomía del agente depende de la criticidad del dominio que toca.

| Nivel | Dominios | Comportamiento |
|-------|----------|----------------|
| **CRÍTICO** | auth, multi-tenancy, RBAC, audit log, liquidaciones, core-models | Solo análisis y propuesta. NO escribir código sin aprobación humana explícita. |
| **MEDIO** | lógica de dominio, integraciones (Moodle/N8N), pipelines | Implementar con checkpoints; surfacear decisiones no obvias para revisión. |
| **BAJO** | CRUDs simples, pages frontend sin lógica crítica, catálogos, configuración | Autonomía total si pasan los tests. Reportar en el resumen. |

Antes de cualquier acción no trivial: identificá el nivel de governance del dominio. En CRÍTICO o sus equivalentes de seguridad, describí el cambio planeado y esperá confirmación antes de escribir.

---

## Decisiones de Arquitectura (ADRs)

Las decisiones grosas que tomamos durante el desarrollo. Algunas están documentadas en [`docs/ARQUITECTURA.md §10`](docs/ARQUITECTURA.md); otras se resolvieron sobre la marcha y las registramos acá para que no se pierdan.

### Decisiones de cimiento (cerradas antes de codear)

Referencia completa en [`docs/ARQUITECTURA.md §10`](docs/ARQUITECTURA.md):

| ADR | Decisión | Por qué |
|-----|----------|---------|
| **ADR-001** | **Auth propio** (JWT + Argon2id + 2FA), no Auth0/Firebase ni Moodle SSO | No acoplar el arranque a la config de Moodle de IT; ADMIN y FINANZAS pueden no ser usuarios Moodle; control total de claims JWT en multi-tenant; sin costo recurrente por usuario. |
| **ADR-002** | **Multi-tenancy row-level** (columna `tenant_id`), no DB-per-tenant | Con un solo tenant inicial, DB-per-tenant es sobreingeniería (migraciones, backups, pooling). Row-level cubre el aislamiento y es el estándar SaaS a esta escala. |
| **ADR-006** | **Materia = catálogo único + Dictado** (no una sola entidad) | Una misma materia se dicta en múltiples carreras/cohortes; separar catálogo de instancia evita duplicar definiciones. |

### Decisiones tomadas durante el desarrollo

| Decisión | Alternativa descartada | Por qué |
|----------|------------------------|---------|
| **AES-256-GCM en reposo para PII** | Hashing (irreversible) | DNI, CUIL, CBU necesitan MOSTRARSE al usuario (perfil, liquidaciones). Hashing es irreversible — no sirve. AES-256-GCM permite descifrado controlado. |
| **TanStack Query para estado servidor** | Redux, Zustand | El 90% del estado de la app es server state (listas, filtros, CRUDs). TanStack Query resuelve caché, refetch, stale-while-revalidate OUT OF THE BOX. Redux/Zustand son genéricos — todo ese boilerplate habría que escribirlo a mano. |
| **Feature-based modules (`features/`)** | `pages/` + `components/` planos | Con 7 roles distintos (ALUMNO→FINANZAS), cada uno con páginas diferentes, la estructura plana degenera en un "cajón de sastre". Feature-based coloca cada dominio junto con sus componentes, hooks, servicios y tipos — escala sin fricción. |
| **Worker async propio (asyncio)** | N8N para la cola de comunicaciones (ADR-003) | La cola de comunicaciones es un loop acotado (Pend→Send→OK/Fail). N8N aportaba complejidad operativa (otro servicio, otra base) sin beneficio real. El worker propio es <200 LOC, testeable, y va en el mismo proceso Docker. |
| **Impersonación vía claim adicional en el JWT** | Token de sesión separado (ADR-004) | Un claim `impersonating_user_id` en el JWT evita tener que manejar una segunda sesión, simplifica el middleware de auditoría (el actor real está siempre en el token), y no requiere estado extra en el cliente. |
| **Padrón versionado (snapshot completo)** | Deltas incrementales (ADR-005) | El padrón se reemplaza COMPLETO en cada import (el Moodle no manda deltas). Versionado con activación/desactivación evita el problema de "entradas huérfanas" y hace trivial el rollback: reactivás la versión anterior. |

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/) + docs/ARQUITECTURA.md   → entender el dominio
2. Identificar el change en CHANGES.md (C-NN) + sus dependencias    → respetar gates
3. Verificar el nivel de governance del dominio                    → CRÍTICO = propuesta primero
4. /opsx:propose C-NN-nombre                                        → proposal + design + specs + tasks
5. Implementar las tasks (cargando skills, Strict TDD)             → respetando las reglas duras
6. /opsx:archive C-NN-nombre + marcar [x] en CHANGES.md            → cerrar el change
```

Aplicá TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.

---

## Referencia Rápida

### 🚀 Arranque — Docker (única forma de levantar el proyecto)

El proyecto está **completamente dockerizado**. Un solo comando levanta todo:

```powershell
cd activia-trace
docker compose up -d
```

Eso arranca 6 servicios en orden: `postgres → migrator → seeder → api → worker → frontend`.
Abrí `http://localhost:3000` (email: `admin@activia.com`, password: `Admin123!`).

> ⚠️ **No hay hot-reload manual.** Si necesitás reconstruir tras cambios: `docker compose up -d --build`.

### Puertos

| Servicio | Puerto |
|----------|--------|
| PostgreSQL | 5433 |
| Backend API | 8000 |
| Frontend (Docker) | 3000 |

### Comandos frecuentes

| Comando | Dónde ejecutarlo | Para qué |
|---------|------------------|----------|
| `docker compose up -d` | raíz del proyecto | Levantar TODO el stack |
| `docker compose down` | raíz del proyecto | Bajar todo el stack |
| `docker compose up -d --build` | raíz del proyecto | Reconstruir y levantar |
| `docker compose logs -f api` | raíz del proyecto | Ver logs del backend |
| `docker compose logs -f frontend` | raíz del proyecto | Ver logs del frontend |
| `pytest -q` | `active-trace\backend\` | Tests backend completos |
| `npm test -- --run` | `active-trace\frontend\` | Tests frontend completos |
| `alembic upgrade head` | backend/ | Correr migraciones pendientes |
| `alembic revision --autogenerate -m "descripcion"` | backend/ | Crear nueva migración |

> ⚠️ **Siempre ejecutar tests desde `backend/`**, nunca desde la raíz del repo. El `conftest.py` resuelve distinto y da falsos fallos.

---

## Problemas Conocidos (Troubleshooting)

Estos son los gotchas que aprendimos con el culo en el fuego. Leelos ANTES de arrancar cualquier implementación para no pisar los mismos errores.

- **`session.get(Model, id)` no respeta tenant scope**: SQLAlchemy `get()` busca por PK y NO aplica el filtro `tenant_id`. Si ves un `session.get(TenantScopedModel, id)` en services o repositories, es un bug de aislamiento multi-tenant. Usar `get_tenant_scoped(session, Model, id, tenant_id)` de `backend/app/core/tenant_aware.py`.

- **Alembic lee `.env` automáticamente**: no hace falta setear `DATABASE_URL` a mano. Está fixeado en `backend/app/alembic/env.py`. Si las migraciones fallan, probablemente no es la URL.

- **PostgreSQL en 5433 en dev**: en Docker el puerto mapeado es `5433:5432`. NO uses 5432 para conexiones locales — apuntan a otro Postgres si tenés uno instalado, o fallan si no.

- **Cifrado de PII (AES-256-GCM)**: DNI, CUIL y CBU se almacenan cifrados. Si un endpoint devuelve texto inentendible (bytes crudos o un `EncryptionError`), probablemente falta llamar a `decrypt_or_none()` en el service. El `bootstrap_admin.py` guarda valores en texto plano ("00000000") que rompen el descifrado — el service debe manejarlo con `try/except`.

- **Tests desde la raíz fallan**: el `conftest.py` de backend/ usa rutas relativas y resuelve distinto si ejecutás desde `active-trace/`. Siempre: `cd active-trace\backend && pytest -q`.

- **`op.execute()` en Alembic**: la API cambió recientemente. No acepta 2 argumentos posicionales. Usar `op.get_bind().execute()` + `bindparams()` con tipo SQL explícito. Ver migraciones 017-019 como referencia.

- **asyncpg `AmbiguousParameterError`**: ocurre cuando un bind param aparece 2+ veces en un mismo query sin tipo explícito. Fix: `.bindparams(sa.bindparam("name", type_=sa.String))`.

- **SQLAlchemy `.is_()` genera sintaxis inválida**: `col.is_(None)` está bien, pero `col.is_(value)` con valor no-NULL genera `IS $param::UUID` (PostgreSQL rechaza). Usar `==` cuando el valor no es None.

- **conftest.py no escala con tablas hardcodeadas**: el cleanup original listaba tablas a mano. Si agregás una tabla y no está en esa lista, los tests dejan estado sucio. Usar `Base.metadata.tables` + TRUNCATE CASCADE dinámico (versión actual ya lo hace).
