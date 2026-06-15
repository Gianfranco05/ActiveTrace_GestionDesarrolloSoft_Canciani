## Why

C-04 (RBAC) completed the backend authZ layer — permissions are seeded, endpoints declare `require_permission(...)`, and the JWT carries user identity with server-side permission resolution. But there is no frontend to consume these endpoints. Every pending change (C-11 análisis, C-12 comunicaciones, C-15 encuentros, etc.) builds on a SPA shell with auth flow, route protection, and permission-aware navigation. C-21 delivers that foundation: the frontend project scaffolding, authentication UI/UX, and guarded layout that ALL subsequent features will import from.

## What Changes

- **Vite + React 18 + TS project** at `frontend/` — no CRA, no legacy config
- **Feature-based folder structure** at `frontend/src/` with `shared/` (cross-cutting) and `features/{name}/` (domain modules)
- **Axios HTTP client** with request interceptor that attaches JWT and response interceptor that handles 401 → transparent refresh → retry
- **Auth context** (`AuthProvider`) — manages current user session, roles, permissions, loading/error states
- **Login screen** — email + password form, consumes `POST /api/auth/login`, stores JWT pair
- **2FA screen** — TOTP code form, consumes `POST /api/auth/2fa/verify`
- **Password recovery screens** — forgot password (email form → `POST /api/auth/forgot`) + reset password (new password form → `POST /api/auth/reset`)
- **ProtectedRoute component** — checks authentication + redirects to `/login` if unauthenticated, renders children if authenticated
- **Permission-based route guard** — `RequirePermission` component that shows 403 page if user lacks the required permission
- **App layout** — sidebar (navigation filtered by permissions) + topbar (user info, avatar, logout button)
- **Logout** — clears session (local state + `POST /api/auth/logout`), redirects to login
- **React Router v6** route tree — layout routes, public routes (`/login`, `/forgot`, `/reset`), protected routes (wildcard `/*` for feature pages)
- **Vitest + React Testing Library** test setup — mocks for auth flow, route guard, interceptor

### Key behaviors
- **Transparent token refresh**: Axios interceptor catches 401, calls `POST /api/auth/refresh` with the stored refresh token, retries the original request. If refresh fails → force logout.
- **Auth context reads from `/api/auth/me`** on app load to hydrate user session. If 401 → unauthenticated state.
- **Permission-based menu**: sidebar renders only navigation items whose required permission the user holds.
- **2FA is a login variant**: login returns `{requires_2fa: true}` → redirect to `/2fa` screen → on 2FA success, session is established.

## Capabilities

### New Capabilities
- `shell-scaffolding`: Project setup — Vite + React 18 + TypeScript + Tailwind CSS + folder structure + build scripts + test runner configuration
- `auth-login`: Login screen with email/password form, Axios interceptor with transparent JWT refresh, auth context/store, user session hydration from `/api/auth/me`
- `auth-2fa-recovery`: 2FA verification screen (TOTP), forgot password screen, reset password screen
- `auth-guards-layout`: ProtectedRoute + RequirePermission components, sidebar/topbar layout with permission-filtered menu, logout flow

### Modified Capabilities
*(None — this is the first frontend change. No existing specs to modify.)*

## Impact

- **New `/frontend/` directory** — Vite project root at repo level
- **`frontend/src/shared/services/api.ts`** — Axios instance with auth interceptor (shared by ALL features)
- **`frontend/src/shared/hooks/useAuth.ts`** — hook to access auth context
- **`frontend/src/shared/components/ProtectedRoute.tsx`** — route guard wrapper
- **`frontend/src/shared/components/RequirePermission.tsx`** — permission guard wrapper
- **`frontend/src/shared/components/AppLayout.tsx`** — sidebar + topbar layout
- **`frontend/src/features/auth/`** — auth domain module: pages (Login, TwoFactor, ForgotPassword, ResetPassword), hooks, components, services, types
- **`frontend/src/App.tsx`** — route tree with React Router v6
- **`frontend/src/main.tsx`** — app entry point
- **Dependencies**: C-04 (RBAC permissions seeded, endpoint guards working), C-03 (JWT auth + 2FA + refresh endpoints exist)
