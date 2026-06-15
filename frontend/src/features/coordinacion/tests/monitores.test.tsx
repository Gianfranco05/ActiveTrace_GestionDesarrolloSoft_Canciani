import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { MonitoresPage } from '@/features/coordinacion/monitores/pages/MonitoresPage';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api', () => ({ default: { get: vi.fn(), post: vi.fn() } }));

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

describe('MonitoresPage - Filters and Tabs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockResolvedValue({ data: { data: [], total: 0, page: 1, total_pages: 1 } });
  });

  it('renders both tabs', () => {
    renderWithProviders(<MonitoresPage />);
    expect(screen.getByText(/General/i)).toBeInTheDocument();
    expect(screen.getByText(/Seguimiento por docente/i)).toBeInTheDocument();
  });

  it('renders filter inputs on General tab', () => {
    renderWithProviders(<MonitoresPage />);
    expect(screen.getByText(/Limpiar filtros/i)).toBeInTheDocument();
    expect(screen.getByText(/Exportar/i)).toBeInTheDocument();
  });
});
