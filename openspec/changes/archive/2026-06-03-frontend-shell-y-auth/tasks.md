## 1. Scaffolding — Vite project + folder structure

- [x] 1.1 Scaffold Vite project: `npm create vite@latest frontend -- --template react-ts` in `active-trace/`
- [x] 1.2 Install production deps: `@tanstack/react-query`, `react-hook-form`, `@hookform/resolvers`, `zod`, `axios`, `react-router-dom`, `clsx`, `tailwind-merge`
- [x] 1.3 Install dev deps: `tailwindcss`, `@tailwindcss/vite`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, ESLint config
- [x] 1.4 Configure `vite.config.ts` — `@vitejs/plugin-react`, path alias `@/` → `src/`, Tailwind plugin
- [x] 1.5 Configure `tsconfig.json` — `strict: true`, `noUnusedLocals`, `noUnusedParameters`, path alias `@/`
- [x] 1.6 Configure `tailwind.config.ts` — content paths, custom color palette (primary, secondary, danger, success)
- [x] 1.7 Configure `postcss.config.js` — Tailwind + autoprefixer
- [x] 1.8 Configure Vitest — `jsdom` environment, setup file with `@testing-library/jest-dom` imports, `@/` alias
- [x] 1.9 Create `frontend/src/` folder structure: `shared/services/`, `shared/hooks/`, `shared/components/ui/`, `shared/types/`, `shared/utils/`, `features/auth/{pages,components,services,hooks,types}/`
- [x] 1.10 Add `postcss.config.js` if needed by Tailwind v4
- [x] 1.11 Verify: `npm run build` passes, `npm run test` runs (no tests yet), `npm run lint` passes

## 2. Shared utilities and types

- [x] 2.1 Create `shared/types/auth.ts` — `User` interface (id, email, name, roles, permissions), `LoginResponse`, `LoginResult` (with `requires_2fa` variant), `AuthState` type
- [x] 2.2 Create `shared/types/nav.ts` — `NavItem` interface (label, path, icon, permission?)
- [x] 2.3 Create `shared/utils/storage.ts` — `getAccessToken()`, `setAccessToken()`, `getRefreshToken()`, `setRefreshToken()`, `clearAuthTokens()`, `STORAGE_KEYS` constant
- [x] 2.4 Create `shared/utils/auth-events.ts` — `AuthEvents` EventEmitter with `force-logout` event, `onForceLogout()` subscribe helper

## 3. Axios HTTP client with auth interceptor

- [x] 3.1 Implement `shared/services/api.ts` — Axios instance with base URL from env var (`VITE_API_URL`)
- [x] 3.2 Implement request interceptor: read access token from storage, attach `Authorization: Bearer` header
- [x] 3.3 Implement response interceptor: catch 401, skip for `/auth/login` and `/auth/refresh`, implement refresh queue pattern (single refresh call, queue pending requests, retry on success)
- [x] 3.4 Handle refresh failure: emit `force-logout` event, reject all queued requests
- [x] 3.5 Write test: `shared/services/api.test.ts` — mock 401 → verify refresh called, mock refresh failure → verify force-logout emitted

## 4. Auth context (AuthProvider + useAuth)

- [x] 4.1 Implement `shared/hooks/useAuth.tsx` — `AuthContext` creation, `AuthProvider` component with `useReducer` for state
- [x] 4.2 Implement auth state machine: initial → loading (mount) → authenticated (200) | unauthenticated (401) | error
- [x] 4.3 Implement `GET /api/auth/me` hydration on mount (via `auth.service.me()`)
- [x] 4.4 Implement `login()` → calls `POST /api/auth/login`, stores tokens, handles `requires_2fa` variant, populates user
- [x] 4.5 Implement `logout()` → calls `POST /api/auth/logout`, clears tokens, resets state, redirects to `/login`
- [x] 4.6 Implement `verify2FA()` → calls `POST /api/auth/2fa/verify`, stores tokens, populates user
- [x] 4.7 Implement `hasPermission()` helper
- [x] 4.8 Subscribe to `AuthEvents.force-logout` in `AuthProvider` (useEffect on mount)
- [x] 4.9 Write test: `shared/hooks/useAuth.test.tsx` — render AuthProvider, mock me() returning user, verify isAuthenticated=true

## 5. Auth service layer

- [x] 5.1 Create `features/auth/types/auth.types.ts` — feature-specific types (LoginPayload, TwoFactorPayload, ForgotPayload, ResetPayload)
- [x] 5.2 Create `features/auth/services/auth.service.ts` — `login(email, password)`, `verify2FA(tempToken, code)`, `forgotPassword(email)`, `resetPassword(token, password)`, `logout()`, `me()` — all typed with Zod schema validation for responses
- [x] 5.3 Write test: `features/auth/services/auth.service.test.ts` — mock each endpoint, verify correct URL and payload

## 6. Login screen

- [x] 6.1 Implement `features/auth/pages/LoginPage.tsx` — centered card layout, renders LoginForm, handles `returnUrl` from query params
- [x] 6.2 Implement `features/auth/components/LoginForm.tsx` — email + password inputs, React Hook Form + Zod validation (email format, password required), loading state on submit, error display on 401, "Olvidé mi contraseña" link
- [x] 6.3 Implement `shared/components/ui/Input.tsx` — reusable input with label, error message, Tailwind styled
- [x] 6.4 Implement `shared/components/ui/Button.tsx` — reusable button with `variant` (primary, secondary, ghost), `isLoading` prop
- [x] 6.5 Write test: `features/auth/pages/LoginPage.test.tsx` — render LoginPage, submit form with valid data, mock login → verify redirect to / or /2fa

## 7. 2FA screen

- [x] 7.1 Implement `features/auth/pages/TwoFactorPage.tsx` — centered card, 6-digit code input, renders TwoFactorForm
- [x] 7.2 Implement `features/auth/components/TwoFactorForm.tsx` — 6-digit TOTP code input, React Hook Form + Zod (6 digits required), loading state, error display
- [x] 7.3 Write test: `features/auth/pages/TwoFactorPage.test.tsx` — render, submit valid code, mock verify2FA → verify redirect to /

## 8. Password recovery screens

- [x] 8.1 Implement `features/auth/pages/ForgotPasswordPage.tsx` — email form + confirmation message state, link to /login
- [x] 8.2 Implement `features/auth/components/ForgotPasswordForm.tsx` — email input, Zod validation, submit → forgotPassword(), show confirmation message
- [x] 8.3 Implement `features/auth/pages/ResetPasswordPage.tsx` — reads `token` from URL params, validates presence, renders form or error
- [x] 8.4 Implement `features/auth/components/ResetPasswordForm.tsx` — new password + confirm password, Zod validation (≥8 chars, match), submit → resetPassword()
- [x] 8.5 Write test: `features/auth/pages/ForgotPasswordPage.test.tsx` — submit email → verify confirmation shown
- [x] 8.6 Write test: `features/auth/pages/ResetPasswordPage.test.tsx` — submit matching passwords → verify redirect to /login

## 9. Route guards

- [x] 9.1 Implement `shared/components/ProtectedRoute.tsx` — reads `isAuthenticated` and `isLoading` from `useAuth()`, redirects to `/login?returnUrl=` if unauthenticated, renders `<Outlet />` if authenticated, loading skeleton while loading
- [x] 9.2 Implement `shared/components/RequirePermission.tsx` — checks `hasPermission(requiredPermission)`, renders children or 403 fallback with "No tenés permisos" message
- [x] 9.3 Write test: `shared/components/ProtectedRoute.test.tsx` — unauthenticated → verify redirect to /login, authenticated → verify children rendered
- [x] 9.4 Write test: `shared/components/RequirePermission.test.tsx` — missing permission → verify 403 rendered, has permission → verify children rendered

## 10. App layout with sidebar and topbar

- [x] 10.1 Implement `shared/components/Sidebar.tsx` — navigation items list, filters by permission via `hasPermission()`, highlights active route via `useLocation()`, renders icons + labels
- [x] 10.2 Implement `shared/components/Topbar.tsx` — user name display, avatar (first letter + colored circle), logout button with confirmation
- [x] 10.3 Implement `shared/components/AppLayout.tsx` — flex layout (sidebar left + main content), renders Sidebar + Topbar + `<Outlet />`, responsive collapse for sidebar
- [x] 10.4 Implement `shared/components/ui/Card.tsx` — reusable card wrapper with optional header, footer, padding props
- [x] 10.5 Write test: `shared/components/AppLayout.test.tsx` — render with mocked auth context, verify sidebar items visible based on permissions, verify logout button works

## 11. App root — route tree and entry point

- [x] 11.1 Implement `frontend/src/main.tsx` — render App wrapped in `BrowserRouter`, `QueryClientProvider` (TanStack), `AuthProvider`
- [x] 11.2 Implement `frontend/src/App.tsx` — React Router v6 route tree: public routes (`/login`, `/2fa`, `/forgot`, `/reset`) in `PublicLayout`, protected routes in `ProtectedRoute` → `AppLayout` with `Outlet`, catch-all 404
- [x] 11.3 Implement `frontend/src/index.css` — Tailwind directives (`@import "tailwindcss"`)
- [x] 11.4 Add a simple Dashboard placeholder page at `features/dashboard/pages/DashboardPage.tsx` — shows "Bienvenido, {user.name}" as a placeholder for C-22+

## 12. Test verification

- [x] 12.1 Run full test suite: `npm run test` from `frontend/` — verify all tests pass
- [x] 12.2 Run `npm run typecheck` — verify no TypeScript errors
- [x] 12.3 Run `npm run lint` — verify no linting errors
- [x] 12.4 Verify `npm run build` produces a clean production build in `frontend/dist/`