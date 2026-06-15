import { useState } from 'react';

import { SalarioBaseForm } from '@/features/finanzas/components/SalarioBaseForm';
import { SalarioPlusForm } from '@/features/finanzas/components/SalarioPlusForm';
import { useSalariosBase, useMutateSalarioBase } from '@/features/finanzas/hooks/useSalariosBase';
import { useSalariosPlus, useMutateSalarioPlus } from '@/features/finanzas/hooks/useSalariosPlus';
import { Alert } from '@/shared/components/ui/Alert';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';

import type { CreateSalarioBasePayload, CreateSalarioPlusPayload } from '@/features/finanzas/types/salario.types';
import type { Column } from '@/shared/components/ui/DataTable';

export function GrillaSalarialPage() {
  const { data: salariosBase, isLoading: loadingBase } = useSalariosBase();
  const { data: salariosPlus, isLoading: loadingPlus } = useSalariosPlus();
  const baseMutate = useMutateSalarioBase();
  const plusMutate = useMutateSalarioPlus();

  const [baseError, setBaseError] = useState<string | null>(null);
  const [plusError, setPlusError] = useState<string | null>(null);
  const [baseSuccess, setBaseSuccess] = useState<string | null>(null);
  const [plusSuccess, setPlusSuccess] = useState<string | null>(null);

  const baseColumns: Column[] = [
    { key: 'rol', header: 'Rol' },
    {
      key: 'monto', header: 'Monto',
      render: (item) => (item.monto as number).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }),
    },
    { key: 'desde', header: 'Desde' },
    {
      key: 'hasta', header: 'Hasta',
      render: (item) => (item.hasta as string | null) ?? 'Vigente',
    },
    {
      key: 'activo', header: 'Estado',
      render: (item) => (
        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
          item.activo ? 'bg-green-100 text-green-700' : 'bg-secondary-100 text-secondary-500'
        }`}>
          {item.activo ? 'Activo' : 'Inactivo'}
        </span>
      ),
    },
  ];

  const plusColumns: Column[] = [
    { key: 'grupo', header: 'Grupo' },
    { key: 'rol', header: 'Rol' },
    { key: 'descripcion', header: 'Descripción' },
    {
      key: 'monto', header: 'Monto',
      render: (item) => (item.monto as number).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }),
    },
    { key: 'desde', header: 'Desde' },
    {
      key: 'hasta', header: 'Hasta',
      render: (item) => (item.hasta as string | null) ?? 'Vigente',
    },
    {
      key: 'activo', header: 'Estado',
      render: (item) => (
        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
          item.activo ? 'bg-green-100 text-green-700' : 'bg-secondary-100 text-secondary-500'
        }`}>
          {item.activo ? 'Activo' : 'Inactivo'}
        </span>
      ),
    },
  ];

  const handleCreateBase = async (data: CreateSalarioBasePayload) => {
    setBaseError(null);
    setBaseSuccess(null);
    try {
      await baseMutate.create.mutateAsync(data);
      setBaseSuccess('Salario base creado correctamente');
    } catch {
      setBaseError('Error al crear el salario base');
    }
  };

  const handleCreatePlus = async (data: CreateSalarioPlusPayload) => {
    setPlusError(null);
    setPlusSuccess(null);
    try {
      await plusMutate.create.mutateAsync(data);
      setPlusSuccess('Salario plus creado correctamente');
    } catch {
      setPlusError('Error al crear el salario plus');
    }
  };

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Grilla Salarial</h1>
        <p className="mt-1 text-sm text-secondary-500">Configuración de salarios base y plus</p>
      </div>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-secondary-900">Salario Base</h2>
        {baseError && <Alert variant="error">{baseError}</Alert>}
        {baseSuccess && <Alert variant="success">{baseSuccess}</Alert>}

        {loadingBase ? (
          <Spinner size="md" />
        ) : (
          <DataTable
            columns={baseColumns}
            data={salariosBase ?? []}
            keyExtractor={(item) => item.id as string}
            emptyMessage="No hay salarios base configurados"
          />
        )}

        <div className="rounded-lg border border-secondary-200 p-4">
          <h3 className="mb-4 text-sm font-medium text-secondary-700">Nuevo Salario Base</h3>
          <SalarioBaseForm onSubmit={handleCreateBase} isSubmitting={baseMutate.create.isPending} />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-secondary-900">Salario Plus</h2>
        {plusError && <Alert variant="error">{plusError}</Alert>}
        {plusSuccess && <Alert variant="success">{plusSuccess}</Alert>}

        {loadingPlus ? (
          <Spinner size="md" />
        ) : (
          <DataTable
            columns={plusColumns}
            data={salariosPlus ?? []}
            keyExtractor={(item) => item.id as string}
            emptyMessage="No hay salarios plus configurados"
          />
        )}

        <div className="rounded-lg border border-secondary-200 p-4">
          <h3 className="mb-4 text-sm font-medium text-secondary-700">Nuevo Salario Plus</h3>
          <SalarioPlusForm onSubmit={handleCreatePlus} isSubmitting={plusMutate.create.isPending} />
        </div>
      </section>
    </div>
  );
}
