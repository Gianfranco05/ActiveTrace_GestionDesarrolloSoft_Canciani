## Context

C-21 is the first frontend change in the activia-trace project. No frontend code exists yet — everything must be scaffolded from scratch. The backend is fully operational with JWT auth (C-03), RBAC permissions (C-04), and a suite of auth endpoints: `POST /api/auth/login`, `/refresh`, `/logout`, `/forgot`, `/reset`, `/2fa/enroll`, `/2fa/verify`, `GET /api/auth/me`.

The KB defines FL-01 (authentication flow: login → 2FA optional → session → menu adaptation → logout), and the frontend architecture §2 (SPA organizada por features, cliente HTTP centralizado). The AGENTS.md and ARQUITECTURA.md hard-code the tech stack: React 18 + TypeScript + Vite + Tailwind + TanStack Query + React Hook Form + Zod + Axios.

Governance is **BAJO** — full autonomy for scaffolding and non-critical UI.

Key constraints:
- No Redux — React Context for auth state (AuthProvider + useAuth)
- Feature-based modules under `features/{name}/`
- All HTTP goes through `@/shared/services/api.ts` Axios instance
- Components <200 LOC, no `any`, no class components
- React Router v6 with layout routes

## Goals / Non-Goals

**Goals:**
- Vite + React 18 + TypeScript project scaffolded at `frontend/`
- `frontend/package.json` with all declared dependencies
- Feature-based folder structure: `shared/` + `features/`
- Axios client with JWT interceptor — transparent refresh on 401, queue requests during refresh
- Auth context (`AuthProvider` + `useAuth`) hydrating from `GET /api/auth/me` on first load
- Login screen: email + password form with React Hook Form + Zod validation, loading/error state
- 2FA screen: TOTP code input, called after login returns `requires_2fa: true`
- Forgot password screen: email form → `POST /api/auth/forgot` → confirmation message
- Reset password screen: token from URL + new password form → `POST /api/auth/reset`
- `ProtectedRoute` component: checks `isAuthenticated`, redirects to `/login` with `returnUrl`
- `RequirePermission` component: checks `user.permissions`, renders 403 fallback if missing
- App layout: sidebar (navigation items filtered by permissions) + topbar (user avatar + logout)
- Logout: clear local state → `POST /api/auth/logout` → redirect to `/login`
- All screens have loading skeleton and error state (no infinite spinners)
- Vitest + React Testing Library configured, with mock server for auth endpoints
- Tests: login flow (success + error), 2FA flow, route guard redirect (unauthenticated), route guard 403 (missing permission), refresh interceptor (success + failure), logout

**Non-Goals:**
- C-22 onwards: any feature page beyond auth (alumnos, materias, comunicaciones, etc.) — C-21 only provides the shell
- Moodle SSO integration — deferred to Fase 2 per ADR-001
- Real API integration in dev — the shell runs against the real backend when available, but dev can work with mocks
- E2E tests (Playwright) — deferred to a later change
- Storybook or component library documentation
- PWAs, SSR, or any build complexity beyond Vite SPA

## Decisions

### D1 — State management: React Context (no Redux, no Zustand)

Auth state is simple: current user, session tokens, loading/error. React Context + a custom provider (`AuthProvider`) is sufficient. No Redux boilerplate, no extra dependency.

```
src/
└── shared/
    └── hooks/
        └── useAuth.ts          ← export { useAuth, AuthProvider, AuthContext }
        └── AuthContext.ts       ← type AuthState, type AuthContextValue
```

**Why not Zustand/Redux?** Auth state is shallow (one user object, one set of tokens). Context re-renders are controlled by splitting `AuthProvider` state access via `useAuth` returning a stable reference. When we reach C-22+ features that need global state (e.g., current tenant config), we add Zustand for THAT purpose — not for auth.

### D2 — Axios interceptor structure

The Axios instance is the single HTTP gateway. Two interceptors:

**Request interceptor** (attach JWT):
```typescript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

**Response interceptor** (catch 401, refresh, retry):
```typescript
let isRefreshing = false;
let pendingQueue: Array<{ resolve, reject }> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status !== 401 || error.config.url?.includes('/auth/login') || error.config.url?.includes('/auth/refresh')) {
      return Promise.reject(error);
    }
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const { access_token } = await api.post('/api/auth/refresh');
        localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access_token);
        pendingQueue.forEach(({ resolve }) => resolve(access_token));
        pendingQueue = [];
        error.config.headers.Authorization = `Bearer ${access_token}`;
        return api(error.config);
      } catch {
        pendingQueue.forEach(({ reject }) => reject(error));
        pendingQueue = [];
        AuthEvents.emit('force-logout');
      } finally {
        isRefreshing = false;
      }
    } else {
      // Queue this request until refresh completes
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve: (token) => {
          error.config.headers.Authorization = `Bearer ${token}`;
          resolve(api(error.config));
        }, reject });
      });
    }
  }
);
```

**Why queue during refresh?** Without the queue, N simultaneous 401s fire N concurrent refresh calls. The pattern: first 401 triggers refresh, all subsequent 401s queue and replay once the new token arrives.

**Why AuthEvents.emit for force-logout?** The interceptor cannot import React context (it would create a circular dependency). A simple EventEmitter decouples the interceptor from `AuthProvider` — `AuthProvider` subscribes on mount.

### D3 — AuthProvider lifecycle

```
App mounts → AuthProvider mounts
  ↓
AuthProvider subscribes to AuthEvents.force-logout
AuthProvider calls GET /api/auth/me
  ↓
  200 → setUser(data), setRoles(data.roles), setPermissions(data.permissions), setIsAuthenticated(true)
  401 → setUser(null), setIsAuthenticated(false)  ← unauthenticated
  error → setError(message)
  pending → setLoading(true)
```

**Auth context value shape:**
```typescript
interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  permissions: string[];
  roles: string[];
  login: (email: string, password: string) => Promise<LoginResult>;
  verify2FA: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (perm: string) => boolean;
}
```

**Why call /api/auth/me on mount?** The JWT expires in 15 minutes. On page refresh, the refresh token is in `localStorage`. The `/api/auth/me` call validates the session server-side. If the access token is expired, the interceptor silently refreshes before `/api/auth/me` retries. If both tokens are invalid, the user gets the unauthenticated state.

### D4 — Login flow with 2FA variant

```
POST /api/auth/login { email, password }
  ↓
  200 → { access_token, refresh_token, requires_2fa: false, user } → hydrate session → redirect to /
  200 → { requires_2fa: true, temp_token } → redirect to /2fa screen
  401 → show error "Credenciales inválidas"
```

**2FA screen:**
```
POST /api/auth/2fa/verify { temp_token, code }
  ↓
  200 → { access_token, refresh_token, user } → hydrate session → redirect to /
  401 → show error "Código inválido"
```

The `temp_token` from the login step is short-lived (5 min) and stored in memory (not localStorage). AuthProvider holds it until 2FA completes or the user navigates away.

### D5 — Route structure (React Router v6)

```typescript
// frontend/src/App.tsx
<Routes>
  <Route element={<PublicLayout />}>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/2fa" element={<TwoFactorPage />} />
    <Route path="/forgot" element={<ForgotPasswordPage />} />
    <Route path="/reset" element={<ResetPasswordPage />} />
  </Route>

  <Route element={<ProtectedLayout />}>          ← checks isAuthenticated
    <Route element={<AppLayout />}>              ← sidebar + topbar
      <Route path="/" element={<DashboardPage />} />
      <Route path="/features/*" element={<RequirePermission component={...} />} />
    </Route>
  </Route>

  <Route path="*" element={<NotFoundPage />} />
</Routes>
```

**ProtectedLayout** = `ProtectedRoute` wrapper around `<Outlet />`. Reads auth context, redirects to `/login?returnUrl={current}` if not authenticated.

**ProtectedRoute (component):**
```typescript
interface ProtectedRouteProps {
  requiredPermission?: string;
  fallback?: ReactNode;  // 403 page or redirect
  children: ReactNode;
}
```

**Why a wrapper layout instead of per-route guards?** Centralizes the auth check. All protected routes exist inside a single layout route. Adding a new feature page means adding a `<Route path="..." element={...} />` inside the layout — no need to remember guard wrappers.

### D6 — Permission-based sidebar menu

```typescript
// frontend/src/shared/components/AppLayout.tsx
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: HomeIcon, permission: null },
  { label: 'Calificaciones', path: '/calificaciones', icon: GradeIcon, permission: 'calificaciones:ver' },
  { label: 'Comunicaciones', path: '/comunicaciones', icon: MessagesIcon, permission: 'comunicacion:enviar' },
  // ... future features
];

// Filter: user.hasPermission(item.permission) for items with a permission
// Render items without permission guard for all authenticated users
```

The sidebar renders only items whose `permission` the user holds. Items with `permission: null` are visible to all authenticated users.

### D7 — Token storage

- **Access token**: `localStorage` — short-lived (15 min), read by the Axios interceptor
- **Refresh token**: `localStorage` — used ONLY by the refresh interceptor, never exposed to components
- **temp_token** (2FA in progress): in-memory (AuthProvider state), never persisted

**Why localStorage over sessionStorage/memory?** The app must survive page refresh (the user refreshes and expects to stay logged in if the refresh token is valid). Cookies with httpOnly are better but require backend changes — deferred to a security hardening change. localStorage is the pragmatic choice for the MVP.

### D8 — File structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css                     ← Tailwind directives
│   ├── vite-env.d.ts
│   │
│   ├── shared/
│   │   ├── services/
│   │   │   └── api.ts                ← Axios instance + interceptor
│   │   ├── hooks/
│   │   │   ├── useAuth.tsx           ← AuthProvider + useAuth
│   │   │   └── AuthContext.ts        ← types only
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── RequirePermission.tsx
│   │   │   ├── AppLayout.tsx         ← sidebar + topbar
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Topbar.tsx
│   │   │   └── ui/                   ← primitive UI (Button, Input, Card, etc.)
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Card.tsx
│   │   │       └── ...
│   │   ├── types/
│   │   │   ├── auth.ts               ← User, LoginResponse, etc.
│   │   │   └── nav.ts                ← NavItem
│   │   └── utils/
│   │       ├── storage.ts            ← localStorage helpers
│   │       └── auth-events.ts        ← EventEmitter for cross-module events
│   │
│   └── features/
│       └── auth/
│           ├── pages/
│           │   ├── LoginPage.tsx
│           │   ├── TwoFactorPage.tsx
│           │   ├── ForgotPasswordPage.tsx
│           │   └── ResetPasswordPage.tsx
│           ├── components/
│           │   ├── LoginForm.tsx
│           │   ├── TwoFactorForm.tsx
│           │   ├── ForgotPasswordForm.tsx
│           │   └── ResetPasswordForm.tsx
│           ├── services/
│           │   └── auth.service.ts   ← login(), verify2FA(), forgot(), reset(), logout(), me()
│           ├── hooks/
│           │   └── useAuthForms.ts   ← form validation schemas (Zod)
│           └── types/
│               └── auth.types.ts     ← feature-specific types
```

### D9 — Test strategy

Tests live in `frontend/src/` alongside source (co-located `.test.tsx` files).

| Test | Layer | Approach |
|------|-------|----------|
| Login flow | Integration | Render LoginPage, mock auth.service → submit form → verify redirect |
| 2FA flow | Integration | Render TwoFactorPage, submit code → verify redirect |
| Route guard redirect | Unit/Integration | Render ProtectedRoute wrapping a child → verify redirect to /login when unauthenticated |
| Route guard 403 | Unit/Integration | Render RequirePermission with missing permission → verify 403 content rendered |
| Refresh interceptor (success) | Unit | Mock 401 response on first call, 200 on refresh → verify original request retries |
| Refresh interceptor (failure) | Unit | Mock 401 on all calls → verify force-logout fires |
| Logout | Integration | Click logout → verify state cleared + redirect |

Mock server: use MSW (Mock Service Worker) or simple Vitest mocks of the auth service layer. The integration tests mock at the service level (not network level) to keep them fast.

### D10 — Styling approach (Tailwind)

- All styles via Tailwind utility classes
- No CSS modules, no styled-components, no inline `style={{}}` (except dynamic values like transforms)
- Color scheme via `tailwind.config.ts` — define primary, secondary, danger, success palettes
- Use Tailwind `darkMode: 'class'` for future dark mode
- Prefer `cn()` utility (clsx + tailwind-merge) for conditional class composition

## Risks / Trade-offs

- **[localStorage for tokens]** → Persists across tabs and survives refresh. Trade-off: XSS vulnerability (a script could read tokens). Mitigation: sanitize all inputs, CSP headers, no `dangerouslySetInnerHTML`. A future hardening change can move tokens to httpOnly cookies with a dedicated auth endpoint.
- **[React Context for auth]** → Simple for current scope. Trade-off: if auth state becomes complex (multi-session, real-time updates, impersonation), Context re-renders could become expensive. Mitigation: split context (user context vs session context), or migrate to Zustand when needed.
- **[Single interceptor queue for refresh]** → First 401 triggers a single refresh call; N concurrent 401s queue. Trade-off: if the refresh endpoint itself returns 401 (stale refresh token), ALL queued requests fail simultaneously. Mitigation: the interceptor catches this case and emits force-logout.
- **[No MSW for now]** — Using Vitest mocks for services is simpler for the current scope. Trade-off: mocks must be updated when the API changes. MSW can be added in a later change.
- **[Co-located tests]** — Tests next to source files (`__tests__/` or `.test.tsx` sibling). Trade-off: Vitest discovers them automatically, no separate test dir to maintain. Favored by the React ecosystem and the project convention.

## Migration Plan

1. Scaffold Vite project: `npm create vite@latest frontend -- --template react-ts`
2. Install dependencies: `npm install @tanstack/react-query react-hook-form @hookform/resolvers zod axios react-router-dom clsx tailwind-merge` + `npm install -D tailwindcss @tailwindcss/vite postcss vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`
3. Configure Tailwind, PostCSS, Vitest
4. Create folder structure (shared, features/auth)
5. Implement in order:
   a. `shared/utils/storage.ts`, `shared/utils/auth-events.ts`
   b. `shared/types/auth.ts`, `shared/types/nav.ts`
   c. `shared/services/api.ts` (Axios + interceptor)
   d. `shared/hooks/useAuth.tsx` (AuthProvider)
   e. `features/auth/services/auth.service.ts`
   f. `features/auth/types/auth.types.ts`
   g. `features/auth/pages/LoginPage.tsx` + form
   h. `features/auth/pages/TwoFactorPage.tsx` + form
   i. `features/auth/pages/ForgotPasswordPage.tsx` + form
   j. `features/auth/pages/ResetPasswordPage.tsx` + form
   k. `shared/components/ProtectedRoute.tsx`
   l. `shared/components/RequirePermission.tsx`
   m. `shared/components/AppLayout.tsx` + Sidebar + Topbar
   n. `shared/components/ui/` (Button, Input, Card)
   o. `App.tsx` (route tree)
   p. `main.tsx` (entry point)
6. Write tests for each step above
7. Verify: `npm run dev`, `npm run test`, `npm run lint`, `npm run typecheck`

## Open Questions

*(None — the scope is well-defined by the AGENTS.md, KB, and working backend endpoints.)*
