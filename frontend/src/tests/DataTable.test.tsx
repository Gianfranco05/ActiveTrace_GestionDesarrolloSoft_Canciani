import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { DataTable, type Column } from '@/shared/components/ui/DataTable';

interface TestItem extends Record<string, unknown> {
  id: string;
  name: string;
  value: number;
}

const columns: Column[] = [
  { key: 'name', header: 'Nombre', sortable: true },
  { key: 'value', header: 'Valor', sortable: true },
];

const data: TestItem[] = [
  { id: '1', name: 'Alpha', value: 100 },
  { id: '2', name: 'Beta', value: 200 },
  { id: '3', name: 'Gamma', value: 50 },
];

describe('DataTable', () => {
  it('renders data rows', () => {
    render(
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders header', () => {
    render(
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Valor')).toBeInTheDocument();
  });

  it('shows empty message when no data', () => {
    render(
      <DataTable
        columns={columns}
        data={[] as TestItem[]}
        keyExtractor={(item) => item.id}
        emptyMessage="Sin registros"
      />
    );

    expect(screen.getByText('Sin registros')).toBeInTheDocument();
  });

  it('renders pagination when pageSize is set', () => {
    render(
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        pageSize={2}
      />
    );

    expect(screen.getByText('Anterior')).toBeInTheDocument();
    expect(screen.getByText('Siguiente')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    render(
      <DataTable
        columns={columns}
        data={[] as TestItem[]}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(
      <DataTable
        columns={columns}
        data={[] as TestItem[]}
        keyExtractor={(item) => item.id}
        isLoading
      />
    );

    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });
});
