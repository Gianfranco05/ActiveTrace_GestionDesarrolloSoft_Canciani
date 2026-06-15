import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useCarreras } from '@/features/admin/hooks/useCarreras';
import { FiltrosLiquidacion } from '@/features/finanzas/components/FiltrosLiquidacion';
import { KPILiquidaciones } from '@/features/finanzas/components/KPILiquidaciones';
import { TablaLiquidaciones } from '@/features/finanzas/components/TablaLiquidaciones';
import { useLiquidaciones, useLiquidacionKPI, useCerrarLiquidacion, useCalcularLiquidacion } from '@/features/finanzas/hooks/useLiquidaciones';
import { Button } from '@/shared/components/ui/Button';
import { ConfirmDialog } from '@/shared/components/ui/ConfirmDialog';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useAuth } from '@/shared/hooks/useAuth';
import { useConfirmDialog } from '@/shared/hooks/useConfirmDialog';

import type { CerrarLiquidacionPayload } from '@/features/finanzas/types/liquidacion.types';

export function LiquidacionesPage() {
  const { hasPermission } = useAuth();
  const canClose = hasPermission('liquidaciones:cerrar');
  const canCalculate = hasPermission('liquidaciones:calcular');

  const [cohorteId, setCohorteId] = useState('');
  const [mes, setMes] = useState('');
  const confirm = useConfirmDialog<null>();

  const filter = useMemo(
    () => ({ cohorte_id: cohorteId || undefined, mes: mes || undefined }),
    [cohorteId, mes]
  );

  const { data: liquidaciones, isLoading: loadingLiquidaciones } = useLiquidaciones(filter);
  const { data: kpi, isLoading: loadingKPI } = useLiquidacionKPI(filter);
  const { data: carreras } = useCarreras();
  const cerrarMutation = useCerrarLiquidacion();
  const calcularMutation = useCalcularLiquidacion();

  const cohortes = useMemo(
    () => (carreras ?? []).map((c) => ({ value: c.id, label: `${c.codigo} - ${c.nombre}` })),
    [carreras]
  );

  const handleCerrar = async () => {
    if (!cohorteId || !mes) {
      toast.error('Seleccioná una cohorte y un mes para cerrar');
      return;
    }
    const payload: CerrarLiquidacionPayload = { cohorte_id: cohorteId, periodo: `${new Date().getFullYear()}-${mes}` };
    try {
      await cerrarMutation.mutateAsync(payload);
      toast.success('Liquidación cerrada correctamente');
      confirm.close();
    } catch {
      toast.error('Error al cerrar la liquidación');
    }
  };

  const handleCalcular = async () => {
    if (!cohorteId || !mes) {
      toast.error('Seleccioná una cohorte y un mes para calcular');
      return;
    }
    const periodo = `${new Date().getFullYear()}-${mes}`;
    try {
      await calcularMutation.mutateAsync({ cohorte_id: cohorteId, periodo });
      toast.success('Liquidación calculada correctamente');
    } catch {
      toast.error('Error al calcular la liquidación');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Liquidaciones</h1>
          <p className="mt-1 text-sm text-secondary-500">Gestión de liquidaciones de honorarios</p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/finanzas/liquidaciones/historial">
            <Button variant="secondary" size="sm">Ver Historial</Button>
          </Link>
          {canCalculate && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleCalcular}
              disabled={!cohorteId || !mes}
              isLoading={calcularMutation.isPending}
            >
              Calcular
            </Button>
          )}
          {canClose && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => confirm.open(null)}
              disabled={!cohorteId || !mes}
            >
              Cerrar Liquidación
            </Button>
          )}
        </div>
      </div>

      <FiltrosLiquidacion
        cohortes={cohortes}
        cohorteId={cohorteId}
        mes={mes}
        onCohorteChange={setCohorteId}
        onMesChange={setMes}
      />

      <KPILiquidaciones kpi={kpi} isLoading={loadingKPI} />

      {loadingLiquidaciones ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <TablaLiquidaciones
          liquidaciones={liquidaciones ?? []}
          isLoading={false}
        />
      )}

      <ConfirmDialog
        isOpen={confirm.isOpen}
        title="Cerrar Liquidación"
        message={
          <div>
            <p>¿Estás seguro de que querés cerrar esta liquidación?</p>
            <p className="mt-2 font-semibold text-danger-600">Esta acción es irreversible.</p>
          </div>
        }
        confirmLabel="Sí, cerrar"
        variant="danger"
        isLoading={cerrarMutation.isPending}
        onConfirm={handleCerrar}
        onCancel={confirm.close}
      />
    </div>
  );
}
