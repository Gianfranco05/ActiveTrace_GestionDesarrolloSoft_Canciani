## ADDED Requirements

### Requirement: ProtectedRoute component
The system SHALL provide a `ProtectedRoute` component that checks `isAuthenticated` from the auth context. If the user is not authenticated, it SHALL redirect to `/login?returnUrl=<current path>`. If authenticated, it SHALL render its children or `<Outlet />`.

#### Scenario: ProtectedRoute renders children when authenticated
- **WHEN** the user is authenticated
- **AND** a ProtectedRoute wraps a child component
- **THEN** the child component SHALL be rendered

#### Scenario: ProtectedRoute redirects to login when unauthenticated
- **WHEN** the user is NOT authenticated
- **AND** the current URL is `/dashboard`
- **THEN** the browser SHALL redirect to `/login?returnUrl=/dashboard`

#### Scenario: ProtectedRoute shows loading state
- **WHEN** the auth context is in loading state
- **THEN** ProtectedRoute SHALL render a loading indicator (spinner or skeleton)
- **AND** SHALL NOT redirect to login

### Requirement: RequirePermission component
The system SHALL provide a `RequirePermission` component that checks whether the current user has the required permission. If the user lacks the permission, it SHALL render a 403 fallback. If the permission check passes, it SHALL render its children.

#### Scenario: RequirePermission renders children when permission is held
- **WHEN** the user has `calificaciones:ver` permission
- **AND** RequirePermission is used with `requiredPermission="calificaciones:ver"`
- **THEN** the children SHALL be rendered

#### Scenario: RequirePermission shows 403 when permission is missing
- **WHEN** the user does NOT have `admin:super` permission
- **AND** RequirePermission is used with `requiredPermission="admin:super"`
- **THEN** a 403 page with "No tenés permisos para acceder a esta sección" SHALL be displayed

#### Scenario: RequirePermission allows null permission (public feature)
- **WHEN** `requiredPermission` is `null` or `undefined`
- **THEN** RequirePermission SHALL render children without checking permissions

### Requirement: App layout with sidebar and topbar
The system SHALL provide an `AppLayout` component that renders a sidebar on the left and a topbar on top, with a main content area in the center. The sidebar SHALL contain navigation links filtered by the user's permissions. The topbar SHALL show the user's name, avatar (first letter), and a logout button.

#### Scenario: AppLayout renders sidebar and topbar
- **WHEN** the user is authenticated and the AppLayout is rendered
- **THEN** a sidebar on the left and a topbar on top SHALL be visible
- **AND** the main content area SHALL render the `<Outlet />`

#### Scenario: Sidebar shows navigation items
- **WHEN** the user has `calificaciones:ver` permission
- **THEN** the sidebar SHALL show a "Calificaciones" navigation link

#### Scenario: Sidebar hides items user lacks permission for
- **WHEN** the user does NOT have `admin:super` permission
- **THEN** the sidebar SHALL NOT show an "Administración" navigation link

#### Scenario: Sidebar shows items without permission guard
- **WHEN** a navigation item has no permission requirement (e.g., "Dashboard")
- **THEN** it SHALL be visible to all authenticated users

#### Scenario: Topbar shows user info
- **WHEN** the user is authenticated
- **THEN** the topbar SHALL display the user's name
- **AND** an avatar showing the first letter of the name

#### Scenario: Topbar logout button
- **WHEN** the user clicks the logout button in the topbar
- **THEN** `logout()` function SHALL be called
- **AND** the browser SHALL redirect to `/login`

#### Scenario: Sidebar highlights active route
- **WHEN** the user is on `/calificaciones`
- **THEN** the "Calificaciones" link in the sidebar SHALL be visually highlighted (active state)

### Requirement: Route tree structure
The application SHALL use React Router v6 with the following route tree:
- Public routes (no auth check): `/login`, `/2fa`, `/forgot`, `/reset`
- Protected routes (require auth): `/` (layout with sidebar)
- Catch-all: `*` → 404 page

Protected routes SHALL be wrapped in ProtectedRoute so that ALL protected routes check authentication in one place.

#### Scenario: Public routes are accessible without auth
- **WHEN** navigating to `/login` without being authenticated
- **THEN** the login page SHALL render without redirect

#### Scenario: Protected routes redirect to login
- **WHEN** navigating to `/` without being authenticated
- **THEN** the browser SHALL redirect to `/login?returnUrl=/`

#### Scenario: Unknown route shows 404
- **WHEN** navigating to `/nonexistent-route`
- **THEN** a 404 page with "Página no encontrada" SHALL be displayed

### Requirement: Logout flow
The logout flow SHALL clear all persisted auth data from localStorage, call `POST /api/auth/logout`, reset the auth context to unauthenticated state, and redirect to `/login`.

#### Scenario: Logout redirects to login
- **WHEN** the user logs out
- **THEN** the browser SHALL navigate to `/login`
- **AND** accessing a protected route SHALL redirect back to login

#### Scenario: Logout clears tokens
- **WHEN** the user logs out
- **THEN** localStorage SHALL NOT contain `access_token` or `refresh_token`

#### Scenario: After logout, /api/auth/me returns 401
- **WHEN** the user logs out
- **AND** the app calls `GET /api/auth/me`
- **THEN** the call SHALL return 401
- **AND** the user SHALL remain on the login page

### Requirement: Navigation item registry
The system SHALL define a navigation item registry (an array of `NavItem` objects) that maps route paths to labels, icons, and optional required permissions. This registry SHALL be the single source of truth for the sidebar menu.

#### Scenario: NavItem with permission guards rendering
- **WHEN** a NavItem has a `permission` field set
- **THEN** it SHALL only appear in the sidebar if `hasPermission(item.permission)` returns `true`

#### Scenario: NavItem without permission renders for all
- **WHEN** a NavItem has `permission: null`
- **THEN** it SHALL appear in the sidebar for all authenticated users
