import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { AsignacionMasivaPage } from '@/features/coordinacion/equipos/pages/AsignacionMasivaPage';
import { ClonarEquipoPage } from '@/features/coordinacion/equipos/pages/ClonarEquipoPage';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api', () => ({ default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() } }));

const mockApi = vi.mocked(api);

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AsignacionMasivaPage - Multi-step wizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockResolvedValue({ data: [] });
  });

  it('renders step 1 of wizard', () => {
    renderWithProviders(<AsignacionMasivaPage />);
    expect(screen.getByText(/^Asignación Masiva$/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Materia/i)).toBeInTheDocument();
  });
});

describe('ClonarEquipoPage - Two-step form', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockResolvedValue({ data: [] });
  });

  it('renders step 1 with origin selection', () => {
    renderWithProviders(<ClonarEquipoPage />);
    expect(screen.getByText(/^Clonar Equipo Docente$/)).toBeInTheDocument();
  });
});
