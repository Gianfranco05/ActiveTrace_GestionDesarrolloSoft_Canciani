# shell-scaffolding Specification

## Purpose
TBD - created by archiving change frontend-shell-y-auth. Update Purpose after archive.
## Requirements
### Requirement: Vite project initialization
The system SHALL scaffold a Vite + React 18 + TypeScript SPA project at `frontend/`. The project SHALL use `@vitejs/plugin-react` for HMR in development.

#### Scenario: Project builds successfully
- **WHEN** running `npm run build` in `frontend/`
- **THEN** the output SHALL be a production build in `frontend/dist/` with no TypeScript errors

#### Scenario: Dev server starts
- **WHEN** running `npm run dev` in `frontend/`
- **THEN** Vite SHALL start a dev server with HMR enabled on a configurable port

### Requirement: TypeScript configuration
The project SHALL have strict TypeScript configuration with `strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`, and path alias `@/` mapping to `src/`.

#### Scenario: Path alias resolves
- **WHEN** a source file imports `@/shared/services/api`
- **THEN** Vite and TypeScript SHALL resolve it to `src/shared/services/api`

#### Scenario: TypeScript strict mode rejects implicit any
- **WHEN** a function parameter lacks a type annotation
- **THEN** the TypeScript compiler SHALL emit an error

### Requirement: Tailwind CSS integration
The project SHALL use Tailwind CSS v4 with the `@tailwindcss/vite` plugin. All styling SHALL use Tailwind utility classes. No CSS modules or CSS-in-JS libraries SHALL be used.

#### Scenario: Tailwind classes render
- **WHEN** a component uses `className="flex items-center p-4"`
- **THEN** the rendered HTML SHALL have the corresponding Tailwind utility styles applied

### Requirement: Folder structure
The project SHALL have the following directory structure under `frontend/src/`:
- `shared/services/` — cross-cutting HTTP and external service clients
- `shared/hooks/` — shared React hooks (useAuth)
- `shared/components/` — shared UI components (ProtectedRoute, AppLayout, ui primitives)
- `shared/types/` — shared TypeScript interfaces and types
- `shared/utils/` — utility functions (storage helpers, event emitter)
- `features/{name}/` — feature-based modules, each with `components/`, `hooks/`, `services/`, `types/`, `pages/`

#### Scenario: Feature module structure exists
- **WHEN** listing the `frontend/src/features/` directory
- **THEN** each feature SHALL have subdirectories for `components`, `hooks`, `services`, `types`, and `pages`

#### Scenario: Shared module structure exists
- **WHEN** listing the `frontend/src/shared/` directory
- **THEN** subdirectories SHALL exist for `services`, `hooks`, `components`, `types`, and `utils`

### Requirement: Dependency declarations
The `frontend/package.json` SHALL declare the following production dependencies:
- `react`, `react-dom` (^18)
- `@tanstack/react-query`
- `react-hook-form`, `@hookform/resolvers`
- `zod`
- `axios`
- `react-router-dom` (^6)
- `clsx`, `tailwind-merge`

And dev dependencies:
- `typescript`, `@types/react`, `@types/react-dom`
- `vite`, `@vitejs/plugin-react`
- `tailwindcss`, `@tailwindcss/vite`
- `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`
- `eslint` + React-specific config

#### Scenario: All dependencies install
- **WHEN** running `npm ci` in `frontend/`
- **THEN** the command SHALL complete without errors

### Requirement: Build scripts
The `frontend/package.json` SHALL define scripts for `dev`, `build`, `preview`, `test`, `lint`, and `typecheck`.

#### Scenario: Build script runs
- **WHEN** running `npm run build` in `frontend/`
- **THEN** Vite SHALL produce optimized output in `frontend/dist/`

#### Scenario: Test script runs
- **WHEN** running `npm run test` in `frontend/`
- **THEN** Vitest SHALL execute all `.test.ts` and `.test.tsx` files and report results

### Requirement: Test runner configuration
Vitest SHALL be configured with `jsdom` environment, global test setup file that imports `@testing-library/jest-dom`, and path alias `@/` matching the TypeScript base URL.

#### Scenario: Vitest runs a component test
- **WHEN** running `npm run test` in `frontend/` with a test file that renders a React component
- **THEN** the test SHALL pass if the rendered output matches the assertion

#### Scenario: jest-dom matchers are available
- **WHEN** a test uses `toBeInTheDocument()` or `toHaveTextContent()`
- **THEN** the matcher SHALL be available without additional imports

### Requirement: Entry point and app shell
`frontend/src/main.tsx` SHALL render the `App` component wrapped in `BrowserRouter`, `QueryClientProvider`, and `AuthProvider`. `frontend/src/App.tsx` SHALL define the route tree with React Router v6 using layout routes.

#### Scenario: App component renders
- **WHEN** the application starts
- **THEN** the route tree SHALL be mounted and React Router SHALL match the initial URL

### Requirement: ESLint configuration
The project SHALL include ESLint with TypeScript rules and React Hooks plugin to enforce `no-unused-vars`, `no-undef`, `react-hooks/exhaustive-deps`, and `@typescript-eslint/no-explicit-any`.

#### Scenario: Lint catches explicit any
- **WHEN** running `npm run lint` with a file that uses `any`
- **THEN** ESLint SHALL emit a warning or error for `@typescript-eslint/no-explicit-any`

