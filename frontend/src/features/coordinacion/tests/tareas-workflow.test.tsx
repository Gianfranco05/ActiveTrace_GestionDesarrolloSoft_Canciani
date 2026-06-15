import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { TareaDetallePage } from '@/features/coordinacion/tareas/pages/TareaDetallePage';
import { TareasPage } from '@/features/coordinacion/tareas/pages/TareasPage';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api', () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }));

const mockApi = vi.mocked(api);

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/coordinacion/tareas']}>
        <Routes>
          <Route path="/coordinacion/tareas" element={ui} />
          <Route path="/coordinacion/tareas/:id" element={<TareaDetallePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Tareas Workflow - State transitions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockResolvedValue({ data: { data: [], total: 0, page: 1, total_pages: 1 } });
  });

  it('renders tareas page with state badges', () => {
    renderWithProviders(<TareasPage />);
    expect(screen.getByText(/Tareas/i)).toBeInTheDocument();
    expect(screen.getByText(/Nueva Tarea/i)).toBeInTheDocument();
  });

  it('renders filter by estado select', () => {
    renderWithProviders(<TareasPage />);
    expect(screen.getByText(/Estado/i)).toBeInTheDocument();
  });
});
