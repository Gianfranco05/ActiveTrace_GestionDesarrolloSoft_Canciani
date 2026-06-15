import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useEstadoAcademico, useMisAvisos, useConfirmarAviso, useMisReservas } from '@/features/alumno/hooks/useAlumno';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { useAuth } from '@/shared/hooks/useAuth';

export function AlumnoDashboardPage() {
  const { user } = useAuth();
  const { data: estado, isLoading: loadingEstado } = useEstadoAcademico();
  const { data: avisosData, isLoading: loadingAvisos } = useMisAvisos(1);
  const { data: reservas, isLoading: loadingReservas } = useMisReservas();
  const confirmar = useConfirmarAviso();

  const avisos = avisosData?.items ?? [];
  const latestAvisos = avisos.slice(0, 3);

  const handleConfirmar = (avisoId: string) => {
    confirmar.mutate(avisoId, {
      onSuccess: () => toast.success('Aviso confirmado'),
      onError: () => toast.error('No se pudo confirmar el aviso'),
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">
          Hola, {user?.name ?? 'Alumno'}
        </h1>
        <p className="mt-1 text-sm text-secondary-500">
          Panel de alumno — consultá tu estado académico, avisos y coloquios.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-secondary-800">Estado Académico</h2>
        {loadingEstado ? (
          <div className="flex justify-center py-6">
            <Spinner size="lg" />
          </div>
        ) : estado ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{estado.resumen.materias_totales}</p>
                <p className="mt-1 text-sm text-secondary-500">Total materias</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-success-600">{estado.resumen.materias_regulares}</p>
                <p className="mt-1 text-sm text-secondary-500">Regulares</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-danger-600">{estado.resumen.materias_en_riesgo}</p>
                <p className="mt-1 text-sm text-secondary-500">En riesgo</p>
              </div>
            </Card>
          </div>
        ) : (
          <Card>
            <p className="text-sm text-secondary-500 py-4 text-center">
              Todavía no hay datos de tu estado académico.
            </p>
          </Card>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-secondary-800">Últimos Avisos</h2>
          <Link to="/alumno/avisos" className="text-sm font-medium text-primary-600 hover:text-primary-700">
            Ver todos
          </Link>
        </div>
        {loadingAvisos ? (
          <div className="flex justify-center py-6">
            <Spinner size="lg" />
          </div>
        ) : latestAvisos.length > 0 ? (
          <div className="space-y-3">
            {latestAvisos.map((aviso) => (
              <Card key={aviso.id}>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h3 className="font-medium text-secondary-900 truncate">{aviso.titulo}</h3>
                    <p className="mt-2 text-xs text-secondary-400">
                      {new Date(aviso.created_at).toLocaleDateString('es-AR')}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <StatusBadge
                      status={aviso.acknowledged ? 'Confirmado' : 'Pendiente'}
                    />
                    {!aviso.acknowledged && (
                      <Button
                        variant="ghost"
                        size="sm"
                        isLoading={confirmar.isPending && confirmar.variables === aviso.id}
                        onClick={() => handleConfirmar(aviso.id)}
                      >
                        Confirmar
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <p className="text-sm text-secondary-500 py-4 text-center">
              No tenés avisos pendientes.
            </p>
          </Card>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-secondary-800">Mis Coloquios</h2>
          <Link to="/alumno/coloquios" className="text-sm font-medium text-primary-600 hover:text-primary-700">
            Ver todos
          </Link>
        </div>
        {loadingReservas ? (
          <div className="flex justify-center py-6">
            <Spinner size="lg" />
          </div>
        ) : reservas && reservas.length > 0 ? (
          <div className="space-y-3">
            {reservas.slice(0, 3).map((reserva: any) => (
              <Card key={reserva.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-secondary-900">
                      {reserva.materia_nombre ?? reserva.materia ?? 'Coloquio'}
                    </p>
                    <p className="mt-1 text-sm text-secondary-500">
                      {reserva.fecha_hora
                        ? new Date(reserva.fecha_hora).toLocaleString('es-AR')
                        : '—'}
                    </p>
                  </div>
                  <StatusBadge
                    status={reserva.estado ?? 'Pendiente'}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <p className="text-sm text-secondary-500 py-4 text-center">
              No tenés reservas de coloquios aún.
            </p>
          </Card>
        )}
      </section>
    </div>
  );
}
