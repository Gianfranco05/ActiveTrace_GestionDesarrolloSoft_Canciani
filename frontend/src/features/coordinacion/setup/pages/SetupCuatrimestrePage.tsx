import { clsx } from 'clsx';
import { useState } from 'react';

import type { AvisoSeveridad } from '@/features/coordinacion/avisos/types/avisos.types';
import { useCrearAviso } from '@/features/coordinacion/avisos/hooks/useAvisos';
import {
  useCrearCohorte,
  useClonarEquipoSetup,
  useCargarPrograma,
  useFechasEvaluaciones,
  useCrearFechaEvaluacion,
  useEliminarFechaEvaluacion,
} from '@/features/coordinacion/setup/hooks/useSetup';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { FileUpload } from '@/shared/components/ui/FileUpload';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import { Textarea } from '@/shared/components/ui/Textarea';

import type { SetupStep } from '@/features/coordinacion/setup/types/setup.types';


const steps: { num: SetupStep; label: string }[] = [
  { num: 1, label: 'Crear Cohorte' },
  { num: 2, label: 'Clonar Equipo' },
  { num: 3, label: 'Ajustar Asignaciones' },
  { num: 4, label: 'Ajustar Vigencias' },
  { num: 5, label: 'Cargar Programas' },
  { num: 6, label: 'Fechas Evaluaciones' },
  { num: 7, label: 'Publicar Aviso' },
];

export function SetupCuatrimestrePage() {
  const [step, setStep] = useState<SetupStep>(1);
  const [cohorteId, setCohorteId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const { mutateAsync: crearCohorte } = useCrearCohorte();
  const { mutateAsync: clonarEq } = useClonarEquipoSetup();
  const { mutateAsync: cargarProg, isPending: uploading } = useCargarPrograma();
  const { mutateAsync: crearFecha } = useCrearFechaEvaluacion();
  const { mutateAsync: eliminarFecha } = useEliminarFechaEvaluacion();
  const { data: fechas, refetch: refetchFechas } = useFechasEvaluaciones(cohorteId ?? '');
  const { mutateAsync: publicarAviso, isPending: publishing } = useCrearAviso();

  const [cohorteForm, setCohorteForm] = useState({ identificador: '', nombre: '', vigencia_desde: '', vigencia_hasta: '', activo: true });
  const [cloneForm, setCloneForm] = useState({ materia_id: '', carrera_id: '', cohorte_origen_id: '' });
  const [asignacionForm, setAsignacionForm] = useState({ materia_id: '', docente_ids: '', rol: '', vigencia_desde: '', vigencia_hasta: '' });
  const [vigenciaForm, setVigenciaForm] = useState({ vigencia_desde: '', vigencia_hasta: '' });
  const [programaForm, setProgramaForm] = useState<{ materia_id: string; titulo: string; archivo: File | null }>({ materia_id: '', titulo: '', archivo: null });
  const [fechaForm, setFechaForm] = useState({ materia_id: '', tipo: 'Parcial', instancia: 1, fecha: '', titulo: '' });
  const [avisoForm, setAvisoForm] = useState({ cuerpo: '', roles: '', severidad: 'Info' as AvisoSeveridad });

  const handleStep = async (nextStep: SetupStep) => {
    setError(null);
    setSuccess(null);

    if (step === 1 && nextStep > 1) {
      try {
        const result = await crearCohorte({
          identificador: cohorteForm.identificador,
          nombre: cohorteForm.nombre,
          vigencia_desde: cohorteForm.vigencia_desde,
          vigencia_hasta: cohorteForm.vigencia_hasta,
          activo: cohorteForm.activo,
        });
        setCohorteId(result.id);
        setSuccess('Cohorte creada correctamente');
      } catch {
        setError('Ya existe una cohorte con ese identificador');
        return;
      }
    }

    if (step === 2 && nextStep > 2) {
      try {
        if (!cohorteId) { setError('Creá la cohorte primero'); return; }
        const result = await clonarEq({ ...cloneForm, cohorte_destino_id: cohorteId });
        setSuccess(`Equipo clonado: ${result.asignaciones_creadas} asignaciones creadas`);
      } catch {
        setError('Error al clonar el equipo');
        return;
      }
    }

    setStep(nextStep);
  };

  const handleFinish = async () => {
    setError(null);
    try {
      await publicarAviso({
        titulo: `Bienvenida al cuatrimestre ${cohorteForm.identificador}`,
        cuerpo: avisoForm.cuerpo,
        alcance: 'PorCohorte',
        rol_destino: avisoForm.roles || null,
        severidad: avisoForm.severidad,
        orden: 1,
        inicio_en: new Date().toISOString(),
        fin_en: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
        activo: true,
        requiere_ack: false,
        cohorte_id: cohorteId ?? undefined,
      });
      setCompleted(true);
      setSuccess('¡Setup completado!');
    } catch {
      setError('Error al publicar el aviso');
    }
  };

  if (completed) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Card>
          <div className="py-12 text-center">
            <Alert variant="success">Setup completado correctamente</Alert>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Setup de Cuatrimestre</h1>

      <div className="overflow-x-auto">
        <div className="flex items-center gap-1 min-w-max">
          {steps.map((s, idx) => (
            <div key={s.num} className="flex items-center">
              <div className={clsx(
                'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-medium',
                step > s.num ? 'bg-success-500 text-white' : step === s.num ? 'bg-primary-600 text-white' : 'bg-secondary-200 text-secondary-600'
              )}>
                {step > s.num ? '✓' : s.num}
              </div>
              <span className={clsx(
                'ml-1 text-xs whitespace-nowrap',
                step === s.num ? 'font-medium text-primary-700' : 'text-secondary-400'
              )}>
                {s.label}
              </span>
              {idx < steps.length - 1 && <div className={clsx('mx-2 h-0.5 w-6', step > s.num ? 'bg-success-500' : 'bg-secondary-200')} />}
            </div>
          ))}
        </div>
      </div>
      <p className="text-sm text-secondary-500">Paso {step} de 7</p>

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <Card>
        <div className="space-y-4">
          {step === 1 && (
            <>
              <h2 className="text-lg font-semibold">Crear Cohorte</h2>
              <Input label="Identificador" value={cohorteForm.identificador} onChange={(e) => setCohorteForm((f) => ({ ...f, identificador: e.target.value }))} placeholder="Ej: AGO-2026" />
              <Input label="Nombre" value={cohorteForm.nombre} onChange={(e) => setCohorteForm((f) => ({ ...f, nombre: e.target.value }))} />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Vigencia Desde" type="date" value={cohorteForm.vigencia_desde} onChange={(e) => setCohorteForm((f) => ({ ...f, vigencia_desde: e.target.value }))} />
                <Input label="Vigencia Hasta" type="date" value={cohorteForm.vigencia_hasta} onChange={(e) => setCohorteForm((f) => ({ ...f, vigencia_hasta: e.target.value }))} />
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={cohorteForm.activo} onChange={(e) => setCohorteForm((f) => ({ ...f, activo: e.target.checked }))} />
                <span className="text-sm text-secondary-700">Activo</span>
              </label>
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="text-lg font-semibold">Clonar Equipo Docente</h2>
              <p className="text-sm text-secondary-500">Origen: {cohorteForm.nombre || 'Nueva cohorte'}</p>
              <Input label="Materia ID" value={cloneForm.materia_id} onChange={(e) => setCloneForm((f) => ({ ...f, materia_id: e.target.value }))} />
              <Input label="Carrera ID" value={cloneForm.carrera_id} onChange={(e) => setCloneForm((f) => ({ ...f, carrera_id: e.target.value }))} />
              <Input label="Cohorte Origen ID" value={cloneForm.cohorte_origen_id} onChange={(e) => setCloneForm((f) => ({ ...f, cohorte_origen_id: e.target.value }))} />
            </>
          )}

          {step === 3 && (
            <>
              <h2 className="text-lg font-semibold">Ajustar Asignaciones</h2>
              <p className="text-sm text-secondary-500">Agregá docentes a la nueva cohorte mediante asignación masiva</p>
              <Input label="Materia ID" value={asignacionForm.materia_id} onChange={(e) => setAsignacionForm((f) => ({ ...f, materia_id: e.target.value }))} />
              <Textarea label="IDs de docentes (separados por coma)" value={asignacionForm.docente_ids} onChange={(e) => setAsignacionForm((f) => ({ ...f, docente_ids: e.target.value }))} />
              <Select
                label="Rol"
                options={[{ value: 'titular', label: 'Titular' }, { value: 'adjunto', label: 'Adjunto' }, { value: 'jtp', label: 'JTP' }, { value: 'ayudante', label: 'Ayudante' }]}
                value={asignacionForm.rol}
                onChange={(e) => setAsignacionForm((f) => ({ ...f, rol: e.target.value }))}
              />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Vigencia Desde" type="date" value={asignacionForm.vigencia_desde} onChange={(e) => setAsignacionForm((f) => ({ ...f, vigencia_desde: e.target.value }))} />
                <Input label="Vigencia Hasta" type="date" value={asignacionForm.vigencia_hasta} onChange={(e) => setAsignacionForm((f) => ({ ...f, vigencia_hasta: e.target.value }))} />
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <h2 className="text-lg font-semibold">Ajustar Vigencias</h2>
              <p className="text-sm text-secondary-500">Actualizá las fechas de vigencia de las asignaciones en lote</p>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Vigencia Desde" type="date" value={vigenciaForm.vigencia_desde} onChange={(e) => setVigenciaForm((f) => ({ ...f, vigencia_desde: e.target.value }))} />
                <Input label="Vigencia Hasta" type="date" value={vigenciaForm.vigencia_hasta} onChange={(e) => setVigenciaForm((f) => ({ ...f, vigencia_hasta: e.target.value }))} />
              </div>
            </>
          )}

          {step === 5 && (
            <>
              <h2 className="text-lg font-semibold">Cargar Programas</h2>
              <p className="text-sm text-secondary-500">Subí el programa oficial de cada materia</p>
              <Input label="Materia ID" value={programaForm.materia_id} onChange={(e) => setProgramaForm((f) => ({ ...f, materia_id: e.target.value }))} />
              <Input label="Título del programa" value={programaForm.titulo} onChange={(e) => setProgramaForm((f) => ({ ...f, titulo: e.target.value }))} />
              <FileUpload
                accept=".pdf,.doc,.docx"
                label="Subir archivo"
                onFileSelect={(file) => setProgramaForm((f) => ({ ...f, archivo: file }))}
              />
              <Button
                onClick={async () => {
                  if (programaForm.archivo) {
                    await cargarProg({ materiaId: programaForm.materia_id, titulo: programaForm.titulo, archivo: programaForm.archivo });
                    setSuccess('Programa cargado correctamente');
                  }
                }}
                isLoading={uploading}
                disabled={!programaForm.archivo}
              >
                Cargar Programa
              </Button>
            </>
          )}

          {step === 6 && (
            <>
              <h2 className="text-lg font-semibold">Fechas de Evaluaciones</h2>

              <div className="grid grid-cols-2 gap-4">
                <Input label="Materia ID" value={fechaForm.materia_id} onChange={(e) => setFechaForm((f) => ({ ...f, materia_id: e.target.value }))} />
                <Select
                  label="Tipo"
                  options={[{ value: 'Parcial', label: 'Parcial' }, { value: 'TP', label: 'Trabajo Práctico' }, { value: 'Coloquio', label: 'Coloquio' }]}
                  value={fechaForm.tipo}
                  onChange={(e) => setFechaForm((f) => ({ ...f, tipo: e.target.value }))}
                />
                <Input label="Instancia" type="number" min={1} value={fechaForm.instancia} onChange={(e) => setFechaForm((f) => ({ ...f, instancia: Number(e.target.value) }))} />
                <Input label="Fecha" type="date" value={fechaForm.fecha} onChange={(e) => setFechaForm((f) => ({ ...f, fecha: e.target.value }))} />
                <Input label="Título" value={fechaForm.titulo} onChange={(e) => setFechaForm((f) => ({ ...f, titulo: e.target.value }))} />
                <div className="flex items-end">
                  <Button onClick={async () => {
                    await crearFecha(fechaForm);
                    refetchFechas();
                    setFechaForm({ materia_id: '', tipo: 'Parcial', instancia: 1, fecha: '', titulo: '' });
                  }}>Agregar</Button>
                </div>
              </div>

              {fechas && fechas.length > 0 && (
                <div className="mt-4">
                  <table className="min-w-full divide-y divide-secondary-200">
                    <thead className="bg-secondary-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">Materia</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">Tipo</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">Instancia</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">Fecha</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">Título</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">Acción</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-secondary-200">
                      {fechas.map((f) => (
                        <tr key={f.id}>
                          <td className="px-4 py-2 text-sm">{f.materia_id}</td>
                          <td className="px-4 py-2 text-sm">{f.tipo}</td>
                          <td className="px-4 py-2 text-sm">{f.instancia}</td>
                          <td className="px-4 py-2 text-sm">{f.fecha}</td>
                          <td className="px-4 py-2 text-sm">{f.titulo}</td>
                          <td className="px-4 py-2">
                            <Button size="sm" variant="danger" onClick={async () => { if (f.id) await eliminarFecha(f.id); }}>
                              Eliminar
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {step === 7 && (
            <>
              <h2 className="text-lg font-semibold">Publicar Aviso de Bienvenida</h2>
              <p className="text-sm text-secondary-500">
                Se publicará un aviso con alcance a la cohorte {cohorteForm.identificador}
              </p>
              <Input label="Título" value={`Bienvenida al cuatrimestre ${cohorteForm.identificador}`} disabled />
              <Textarea label="Cuerpo" rows={6} value={avisoForm.cuerpo} onChange={(e) => setAvisoForm((f) => ({ ...f, cuerpo: e.target.value }))} />
              <Input label="Roles destinatarios (separados por coma)" value={avisoForm.roles} onChange={(e) => setAvisoForm((f) => ({ ...f, roles: e.target.value }))} placeholder="profesor, alumno" />
              <Select
                label="Severidad"
                options={[{ value: 'Info', label: 'Informativa' }, { value: 'Advertencia', label: 'Advertencia' }, { value: 'Critico', label: 'Crítico' }]}
                value={avisoForm.severidad}
                onChange={(e) => setAvisoForm((f) => ({ ...f, severidad: e.target.value as AvisoSeveridad }))}
              />
            </>
          )}

          <div className="flex justify-between pt-4">
            <Button variant="secondary" onClick={() => setStep((s) => Math.max(s - 1, 1) as SetupStep)} disabled={step === 1}>
              Anterior
            </Button>
            {step < 7 ? (
              <Button onClick={() => handleStep((step + 1) as SetupStep)}>
                Siguiente
              </Button>
            ) : (
              <Button onClick={handleFinish} isLoading={publishing}>
                Finalizar Setup
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
