## ADDED Requirements

### Requirement: Axios HTTP client with JWT interceptor
The system SHALL provide a centralized Axios instance at `@/shared/services/api` with two interceptors:

- **Request interceptor**: SHALL read the access token from localStorage and attach it as `Authorization: Bearer <token>` header
- **Response interceptor**: SHALL catch 401 responses, attempt a transparent token refresh via `POST /api/auth/refresh`, and retry the original request. If refresh fails, SHALL emit a `force-logout` event that clears the session.

#### Scenario: Request interceptor attaches token
- **WHEN** a request is made through the Axios instance
- **AND** an access token exists in localStorage
- **THEN** the request SHALL include an `Authorization` header with `Bearer <token>`

#### Scenario: Response interceptor refreshes on 401
- **WHEN** a request returns 401
- **AND** the refresh token is valid
- **THEN** the interceptor SHALL call `POST /api/auth/refresh`
- **AND** retry the original request with the new access token

#### Scenario: Response interceptor logs out on refresh failure
- **WHEN** a request returns 401
- **AND** the refresh token is also expired or invalid
- **THEN** the interceptor SHALL emit `force-logout`
- **AND** all pending requests during refresh SHALL be rejected

#### Scenario: Login and refresh endpoints skip interceptor
- **WHEN** a request targets `/api/auth/login` or `/api/auth/refresh`
- **THEN** the response interceptor SHALL NOT attempt refresh (to avoid infinite loops)

#### Scenario: Concurrent 401s do not trigger multiple refresh calls
- **WHEN** N simultaneous requests receive 401
- **THEN** only ONE refresh call SHALL be made
- **AND** all N requests SHALL be queued and retried after the refresh completes

### Requirement: Auth context (AuthProvider)
The system SHALL provide `AuthProvider` (React Context) at `@/shared/hooks/useAuth` that manages the current user session, authentication state, loading state, and error state. It SHALL hydrate the session by calling `GET /api/auth/me` on mount.

#### Scenario: AuthProvider hydrates from /api/auth/me
- **WHEN** the application mounts
- **AND** a valid access or refresh token exists
- **THEN** `AuthProvider` SHALL call `GET /api/auth/me`
- **AND** `isAuthenticated` SHALL become `true`
- **AND** `user` SHALL contain the response data (user_id, email, name, roles, permissions)

#### Scenario: AuthProvider shows loading during hydration
- **WHEN** the application mounts
- **AND** `GET /api/auth/me` is in progress
- **THEN** `isLoading` SHALL be `true`

#### Scenario: AuthProvider shows unauthenticated on 401
- **WHEN** `GET /api/auth/me` returns 401
- **THEN** `isAuthenticated` SHALL be `false`
- **AND** `user` SHALL be `null`
- **AND** `isLoading` SHALL be `false`

#### Scenario: AuthProvider handles force-logout event
- **WHEN** the `force-logout` event is emitted (from the Axios interceptor)
- **THEN** the session SHALL be cleared
- **AND** the user SHALL be redirected to `/login`

### Requirement: useAuth hook
The system SHALL export a `useAuth` hook that returns the AuthContext value: `user`, `isLoading`, `isAuthenticated`, `error`, `permissions`, `roles`, `login()`, `verify2FA()`, `logout()`, `hasPermission()`.

#### Scenario: useAuth returns auth state
- **WHEN** a component calls `useAuth()`
- **THEN** it SHALL receive the current auth context value
- **AND** the component SHALL re-render when the auth state changes

#### Scenario: useAuth throws outside AuthProvider
- **WHEN** a component calls `useAuth()` outside of `AuthProvider`
- **THEN** it SHALL throw a descriptive error

### Requirement: Login function
The `login()` function SHALL call `POST /api/auth/login` with `email` and `password`. If the response indicates `requires_2fa: true`, it SHALL store a temporary token in memory and return `{ requires_2fa: true }`. If 2FA is not required, it SHALL store the access and refresh tokens and hydrate the user session.

#### Scenario: Login succeeds without 2FA
- **WHEN** `login("user@test.com", "correct-password")` is called
- **AND** the backend returns `{ access_token, refresh_token, requires_2fa: false, user }`
- **THEN** `access_token` and `refresh_token` SHALL be stored in localStorage
- **AND** `isAuthenticated` SHALL become `true`
- **AND** `user` SHALL be populated

#### Scenario: Login fails with invalid credentials
- **WHEN** `login("user@test.com", "wrong-password")` is called
- **AND** the backend returns 401
- **THEN** the promise SHALL reject with an error message "Credenciales inválidas"
- **AND** `isAuthenticated` SHALL remain `false`

#### Scenario: Login returns requires_2fa
- **WHEN** `login("user@test.com", "password")` is called
- **AND** the backend returns `{ requires_2fa: true, temp_token: "..." }`
- **THEN** the promise SHALL resolve with `{ requires_2fa: true }`
- **AND** the temp_token SHALL be stored in memory (not localStorage)

### Requirement: Logout function
The `logout()` function SHALL call `POST /api/auth/logout`, clear the access and refresh tokens from localStorage, set `isAuthenticated` to `false`, set `user` to `null`, and redirect to `/login`.

#### Scenario: Logout clears session
- **WHEN** `logout()` is called
- **THEN** `POST /api/auth/logout` SHALL be called
- **AND** tokens SHALL be removed from localStorage
- **AND** `isAuthenticated` SHALL be `false`
- **AND** `user` SHALL be `null`

### Requirement: hasPermission function
The `hasPermission()` function SHALL check whether the current user's permissions array includes the given permission string. The check SHALL be case-sensitive.

#### Scenario: hasPermission returns true
- **WHEN** `hasPermission("calificaciones:ver")` is called
- **AND** the user's permissions include `"calificaciones:ver"`
- **THEN** the function SHALL return `true`

#### Scenario: hasPermission returns false
- **WHEN** `hasPermission("admin:super")` is called
- **AND** the user's permissions do NOT include `"admin:super"`
- **THEN** the function SHALL return `false`

#### Scenario: hasPermission returns false when not authenticated
- **WHEN** `hasPermission("any:permission")` is called
- **AND** the user is not authenticated
- **THEN** the function SHALL return `false`

### Requirement: Login screen
The login screen (`/login`) SHALL render a centered card with email and password inputs, a "Iniciar sesión" submit button, a link to "Olvidé mi contraseña", and the application logo/name. The form SHALL use React Hook Form with Zod validation.

#### Scenario: Login form renders
- **WHEN** navigating to `/login`
- **THEN** email input, password input, submit button, and "Olvidé mi contraseña" link SHALL be visible

#### Scenario: Login form validates email format
- **WHEN** the user types an invalid email and submits
- **THEN** an error message "Email inválido" SHALL be displayed below the email input

#### Scenario: Login form validates password not empty
- **WHEN** the user submits with an empty password
- **THEN** an error message "La contraseña es requerida" SHALL be displayed

#### Scenario: Login form shows loading state
- **WHEN** the user submits valid credentials
- **AND** the request is in progress
- **THEN** the submit button SHALL be disabled
- **AND** a spinner or "Iniciando sesión..." text SHALL be shown

#### Scenario: Login form shows error message
- **WHEN** the login request fails with 401
- **THEN** an error message "Credenciales inválidas" SHALL be displayed above the form

#### Scenario: Login redirects to /2fa when 2FA required
- **WHEN** the login response indicates `requires_2fa: true`
- **THEN** the browser SHALL navigate to `/2fa`

#### Scenario: Login redirects to / on success
- **WHEN** login succeeds without 2FA requirement
- **THEN** the browser SHALL navigate to `/`

### Requirement: Auth service layer
The system SHALL provide an auth service module at `@/features/auth/services/auth.service.ts` with functions: `login(email, password)`, `verify2FA(tempToken, code)`, `forgotPassword(email)`, `resetPassword(token, password)`, `logout()`, `me()`.

#### Scenario: me() returns current user
- **WHEN** `me()` is called with a valid session
- **THEN** the call SHALL GET `/api/auth/me`
- **AND** return the user object

#### Scenario: me() returns 401 when not authenticated
- **WHEN** `me()` is called without a valid session
- **THEN** the call SHALL return 401
