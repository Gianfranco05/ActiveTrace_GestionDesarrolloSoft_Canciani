import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>
  );
}

const mockMaterias = [
  { id: 'mat-1', nombre: 'Matemática', comision: 'A-101' },
  { id: 'mat-2', nombre: 'Física', comision: 'B-202' },
];

describe('MateriaSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(api.get).mockImplementation(() => new Promise(() => {}));

    renderWithProviders(
      <MateriaSelector value="" onChange={() => {}} />
    );

    expect(screen.getByText('Cargando materias...')).toBeInTheDocument();
  });

  it('renders options after loading', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: mockMaterias });

    renderWithProviders(
      <MateriaSelector value="" onChange={() => {}} />
    );

    await waitFor(() => {
      expect(screen.getByText('Matemática — A-101')).toBeInTheDocument();
    });

    expect(screen.getByText('Física — B-202')).toBeInTheDocument();
  });

  it('calls onChange when selection changes', async () => {
    const onChange = vi.fn();
    vi.mocked(api.get).mockResolvedValue({ data: mockMaterias });

    const user = userEvent.setup();

    renderWithProviders(
      <MateriaSelector value="" onChange={onChange} />
    );

    await waitFor(() => {
      expect(screen.getByText('Matemática — A-101')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'mat-1');

    expect(onChange).toHaveBeenCalledWith('mat-1');
  });

  it('shows error message on API failure', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('Network error'));

    renderWithProviders(
      <MateriaSelector value="" onChange={() => {}} />
    );

    await waitFor(() => {
      expect(screen.getByText('Error al cargar materias')).toBeInTheDocument();
    });
  });
});
