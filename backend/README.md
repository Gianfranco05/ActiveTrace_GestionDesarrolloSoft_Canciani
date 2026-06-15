# activia-trace — Backend

FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Alembic. API REST multi-tenant para gestión académica y trazabilidad.

## 🐳 Docker (recomendado)

El backend se levanta con el `docker-compose.yml` de la raíz:

```powershell
cd ..
docker compose up -d
```

Esto levanta PostgreSQL, corre migraciones, y arranca la API en `http://localhost:8000`. **No necesitás hacer nada más.**

---

## 🛠️ Desarrollo manual (con hot-reload)

Si necesitás modificar código con hot-reload, seguí estos pasos.

### Requisitos

| Herramienta | Versión mínima | Para qué |
|-------------|---------------|----------|
| Python | 3.13 | Runtime |
| Docker Desktop | — | PostgreSQL |
| Git | — | Clonar |

---

### Primer arranque (desde cero)

#### 1. Clonar y posicionarse

```powershell
git clone <repo-url> activia-trace
cd activia-trace\backend
```

#### 2. Configurar variables de entorno

```powershell
Copy-Item .env.example .env
```

Editá **sí o sí** estas dos claves en `.env`:

```ini
# SECRET_KEY: al menos 32 caracteres
SECRET_KEY="una-clave-random-de-al-menos-32-caracteres"

# ENCRYPTION_KEY: EXACTAMENTE 32 caracteres (⚠️ ni 31, ni 33)
ENCRYPTION_KEY="exactamente-32-caracteres-ahora!"
```

El `DATABASE_URL` por defecto apunta a `localhost:5433` (puerto expuesto por el container de Docker). Si usás `docker compose up api`, cambiá el host a `postgres`.

#### 3. Crear entorno virtual e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

#### 4. Levantar PostgreSQL con Docker

```powershell
# Desde la raíz del proyecto (activia-trace/)
cd ..
docker compose up -d postgres
cd backend
```

Esto levanta PostgreSQL 16 en `localhost:5433`:

| Campo | Valor |
|-------|-------|
| Host | `localhost` / `127.0.0.1` |
| Puerto | `5433` |
| Usuario | `user` |
| Password | `password` |
| Base de datos | `activia_trace` |

#### 5. Crear base de datos de test

```powershell
docker exec -it active-trace-postgres-1 psql -U user -d activia_trace -c "CREATE DATABASE activia_trace_test"
```

#### 6. Ejecutar migraciones

```powershell
alembic upgrade head
```

#### 7. Levantar la API

```powershell
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

API en `http://localhost:8000`. Health check en `GET /health`.

---

### Arranque diario (ya configurado)

```powershell
cd activia-trace\backend

# 1. PostgreSQL corriendo (si no, docker compose up -d postgres desde la raíz)
# 2. Activá venv y arrancá
.\.venv\Scripts\Activate.ps1
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

---

## Comandos útiles

### Tests

```powershell
# Suite completa
pytest -q

# Un archivo específico
pytest tests/test_auditoria_panel_acciones.py -v

# Con cobertura
pytest -q --cov=app --cov-report=term

# Solo los tests que fallaron la última vez
pytest --lf
```

### Linting

```powershell
ruff check app/
ruff check app/ --fix          # auto-corrige lo que puede
```

### Migraciones

```powershell
alembic upgrade head            # aplicar pendientes
alembic downgrade -1            # deshacer la última
alembic history                 # ver historial
alembic current                 # ver revisión actual
```

### Docker

```powershell
# Desde la raíz del proyecto
docker compose up -d postgres    # levantar PostgreSQL
docker compose down              # apagar todo
docker compose down -v           # apagar Y borrar datos (⚠️)
```

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── api/v1/routers/     ← Endpoints REST
│   ├── core/               ← Config, seguridad, dependencias
│   ├── models/             ← Modelos SQLAlchemy
│   ├── repositories/       ← Acceso a datos (NUNCA desde services)
│   ├── schemas/            ← Pydantic DTOs (extra='forbid')
│   ├── services/           ← Lógica de negocio
│   ├── integrations/       ← Clientes externos (Moodle, N8N)
│   ├── workers/            ← Background jobs (comunicaciones)
│   └── main.py             ← FastAPI app factory
├── alembic/                ← Migraciones
├── tests/                  ← Tests con pytest
├── Dockerfile              ← Imagen Docker
├── pyproject.toml          ← Dependencias + config
└── .env                    ← Variables de entorno (gitignored)
```
