# Materia
Gestión de Desarrollo de Software
# Profesores
- Juan Cruz Robledo
- Alberto Cortez

# Integrantes
- Gianfranco Canciani
- Lucas Pujada
- Bruno Rivera
- Julio Leiva

# activia-trace

Plataforma de gestión académica y trazabilidad **multi-tenant** que opera como capa de orquestación sobre Moodle. Consolida calificaciones, detecta atrasos, gestiona comunicación saliente con aprobación, equipos docentes, encuentros, coloquios, liquidaciones de honorarios y auditoría completa. Cada institución es un tenant aislado.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.13 · FastAPI (async) · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 |
| **Frontend** | React 18 · TypeScript · Vite · TanStack Query · Tailwind CSS |
| **Auth** | JWT (access + refresh rotation) · Argon2id · AES-256 para PII |
| **Infra** | Docker · docker-compose · nginx |
| **Testing** | pytest (≥80% coverage) · vitest + Testing Library |

---

## 🚀 Arranque rápido (Docker — recomendado)

Un solo comando levanta TODO:

```powershell
git clone <repo-url> activia-trace
cd activia-trace

# Copiá y editá el .env del backend (SOLO la primera vez)
Copy-Item backend\.env.example backend\.env
# ⚠️ Editá SECRET_KEY y ENCRYPTION_KEY en backend\.env

# ¡Un comando!
docker compose up -d
```

**Eso es todo.** Te levanta 6 servicios en orden:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **postgres** | `5433` | PostgreSQL 16 |
| **migrator** | — | Corre `alembic upgrade head` y sale |
| **seeder** | — | Crea el admin por defecto (idempotente) y sale |
| **api** | `8000` | FastAPI (backend) |
| **worker** | — | Background jobs (comunicaciones) |
| **frontend** | `3000` | React SPA servido por nginx |

Abrí `http://localhost:3000` y logeate con:

| Campo | Valor |
|-------|-------|
| **Email** | `admin@activia.com` |
| **Password** | `Admin123!` |

> El seeder es **idempotente**: si el admin ya existe, no hace nada. Podés correr `docker compose up -d` mil veces sin problema.

---

## 🔁 Arranque diario (Docker)

```powershell
cd activia-trace
docker compose up -d
```

Si ya levantaste antes, Docker reusa lo que está buildeado. Solo reconstruye si cambió el código:

```powershell
docker compose up -d --build
```

---

## ⚙️ Configuración inicial (primera vez)

### 1. `backend/.env`

```powershell
Copy-Item backend\.env.example backend\.env
```

Editá estas dos claves en `backend\.env`:

```ini
# SECRET_KEY: al menos 32 caracteres
SECRET_KEY="una-clave-random-de-al-menos-32-caracteres"

# ENCRYPTION_KEY: EXACTAMENTE 32 caracteres (⚠️ ni 31, ni 33)
ENCRYPTION_KEY="exactamente-32-caracteres-ahora!"
```

### 2. Primer usuario ADMIN

El seeder lo crea automáticamente. Credenciales:

| Campo | Valor |
|-------|-------|
| Email | `admin@activia.com` |
| Password | `Admin123!` |

Si necesitás crearlo manualmente (sin Docker), conectate a PostgreSQL:

```powershell
docker exec -it active-trace-postgres-1 psql -U user -d activia_trace
```

```sql
-- Generar hash: python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('Admin123!'))"
INSERT INTO auth_user (id, tenant_id, email, password_hash)
SELECT gen_random_uuid(), id, 'admin@activia.com', '<hash-argon2>'
FROM tenant WHERE slug = 'default';
```

---

## 📋 Comandos esenciales

### Docker

```powershell
docker compose up -d              # Levantar todo
docker compose down               # Apagar todo
docker compose down -v            # Apagar Y borrar datos (⚠️)
docker compose logs api           # Logs del backend
docker compose logs frontend      # Logs del frontend
docker compose build --no-cache   # Rebuildear desde cero
```

### Backend (desarrollo manual)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

# Tests (siempre desde backend/)
pytest -q                                # suite completa
pytest tests/test_archivo.py -v          # archivo específico
pytest -q --cov=app --cov-report=term    # con cobertura

# Migraciones
alembic upgrade head       # aplicar pendientes
alembic downgrade -1       # deshacer última
alembic current            # revisión actual

# Linting
ruff check app/
ruff check app/ --fix
```

### Frontend (desarrollo manual)

```powershell
cd frontend

npm run dev          # servidor de desarrollo (HMR)
npm test             # tests (vitest)
npm run check        # typecheck + lint
npm run build        # build de producción
```

---

## 🗂️ Estructura del proyecto

```
activia-trace/
├── backend/                    ← API FastAPI
│   ├── app/
│   │   ├── api/v1/routers/     ← Endpoints REST
│   │   ├── core/               ← Config, seguridad, dependencias
│   │   ├── models/             ← Modelos SQLAlchemy
│   │   ├── repositories/       ← Acceso a datos
│   │   ├── schemas/            ← Pydantic DTOs
│   │   ├── services/           ← Lógica de negocio
│   │   ├── integrations/       ← Clientes externos (Moodle, N8N)
│   │   └── workers/            ← Background jobs
│   ├── alembic/                ← Migraciones
│   ├── tests/                  ← Tests con pytest
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   ← SPA React
│   ├── src/
│   │   ├── features/           ← Módulos por dominio
│   │   │   ├── admin/          ← Admin: estructura, usuarios, auditoría
│   │   │   ├── auth/           ← Login, 2FA, guards
│   │   │   ├── coordinacion/   ← Equipos, avisos, tareas, coloquios
│   │   │   ├── dashboard/      ← Dashboard por rol
│   │   │   └── finanzas/       ← Liquidaciones, facturas, grilla
│   │   └── shared/             ← Componentes, hooks, tipos compartidos
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── knowledge-base/             ← Documentación de dominio
├── docs/                       ← Arquitectura y PRD
├── openspec/                   ← Especificaciones y changes archivados
├── docker-compose.yml          ← Servicios (postgres, api, worker, frontend)
├── AGENTS.md                   ← Instrucciones para agentes AI
├── CHANGES.md                  ← Roadmap de implementación (24 changes ✅)
└── README.md                   ← Este archivo
```

---

## 📚 Documentación

| Archivo | Contenido |
|---------|-----------|
| `docs/ARQUITECTURA.md` | Stack, Clean Architecture, estructura de directorios, seguridad |
| `docs/PRD.md` | Requerimientos de producto y no funcionales |
| `knowledge-base/` | 11 archivos de dominio: actores, reglas de negocio, modelo de datos, flujos, decisiones, historias de usuario |
| `AGENTS.md` | Reglas duras del proyecto, skills disponibles, governance |
| `CHANGES.md` | Roadmap completo de 24 changes implementados |
| `backend/README.md` | Setup detallado del backend |
| `frontend/README.md` | Setup detallado del frontend |

---

## 🔐 Credenciales por defecto (desarrollo)

| Servicio | Usuario | Password | Puerto |
|----------|---------|----------|--------|
| PostgreSQL | `user` | `password` | `5433` |
| API | — | — | `8000` (Docker) |
| Frontend | — | — | `3000` (Docker) / `5173` (dev) |

---

## ⚠️ Reglas duras

- **No build automático** sin pedido explícito
- **No commits** sin pedido explícito
- Tests **siempre desde `backend/`** con `pytest -q`
- Nunca lógica de negocio en routers, nunca acceso directo a DB desde services
- `snake_case` en Python, `PascalCase` en componentes React
- Schemas Pydantic con `extra='forbid'`
- Soft delete siempre, identidad desde JWT verificado, multi-tenancy row-level

Reglas completas en `AGENTS.md`.
