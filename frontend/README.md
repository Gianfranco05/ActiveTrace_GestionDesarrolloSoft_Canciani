# activia-trace — Frontend

React 18 + TypeScript + Vite + TanStack Query + Tailwind CSS. SPA por features para la plataforma de gestión académica.

## 🐳 Docker (recomendado)

El frontend se levanta con el `docker-compose.yml` de la raíz:

```powershell
cd ..
docker compose up -d
```

Esto buildea el frontend, lo sirve con nginx, y lo expone en `http://localhost:3000`. **No necesitás hacer nada más.** Las llamadas `/api/*` se proxean automáticamente al backend.

---

## 🛠️ Desarrollo manual (con HMR)

Si necesitás hot-reload para desarrollar, seguí estos pasos.

### Requisitos

| Herramienta | Versión mínima | Para qué |
|-------------|---------------|----------|
| Node.js | 20+ | Runtime |
| npm | 10+ | Gestor de paquetes |
| Backend | corriendo en `:8000` | API |

> El backend **tiene que estar corriendo** para que el frontend funcione. Podés usar `docker compose up -d` desde la raíz o levantarlo manualmente.

---

### Primer arranque (desde cero)

#### 1. Posicionarse

```powershell
cd activia-trace\frontend
```

#### 2. Configurar variables de entorno

```powershell
Copy-Item .env.example .env
```

El `.env` ya apunta a `http://localhost:8000`. Solo cambiá la URL si tu backend corre en otro puerto:

```ini
VITE_API_URL=http://localhost:8000
```

#### 3. Instalar dependencias

```powershell
npm install
```

#### 4. Levantar el servidor de desarrollo

```powershell
npm run dev
```

Frontend en `http://localhost:5173` con HMR (Hot Module Replacement).

#### 5. Verificar

```powershell
npm run check        # typecheck + lint
npm test             # tests
```

---

### Arranque diario (ya configurado)

```powershell
cd activia-trace\frontend
npm run dev
```

Si necesitás actualizar dependencias:

```powershell
npm install
```

---

## Comandos útiles

| Comando | Qué hace |
|---------|----------|
| `npm run dev` | Servidor de desarrollo con HMR |
| `npm run build` | Build de producción (`tsc` + `vite build`) |
| `npm run preview` | Previsualizar el build de producción |
| `npm test` | Correr tests (vitest) |
| `npm run test:watch` | Tests en modo watch |
| `npm run typecheck` | Solo chequeo de tipos (`tsc --noEmit`) |
| `npm run lint` | Linting con ESLint |
| `npm run lint:fix` | Linting + auto-corrección |
| `npm run check` | `typecheck` + `lint` juntos |

---

## Primer login (ADMIN)

Después de que las migraciones hayan corrido, conectate a PostgreSQL:

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

## Estructura del proyecto

```
frontend/
├── src/
│   ├── features/           ← Módulos por dominio
│   │   ├── admin/          ← Admin: estructura, usuarios, auditoría
│   │   ├── auth/           ← Login, 2FA, guards
│   │   ├── coordinacion/   ← Equipos, avisos, tareas, coloquios
│   │   ├── dashboard/      ← Dashboard por rol
│   │   └── finanzas/       ← Liquidaciones, facturas, grilla
│   ├── shared/             ← Componentes, hooks y tipos compartidos
│   ├── tests/              ← Tests con vitest + Testing Library
│   └── main.tsx            ← Entry point
├── Dockerfile              ← Imagen Docker (Node build → nginx serve)
├── nginx.conf              ← Config de nginx (SPA + /api proxy)
├── .env.example            ← Template de variables de entorno
├── package.json            ← Dependencias y scripts
├── tailwind.config.ts      ← Config de Tailwind
├── tsconfig.json           ← Config de TypeScript
└── vite.config.ts          ← Config de Vite (HMR + proxy /api en dev)
```
