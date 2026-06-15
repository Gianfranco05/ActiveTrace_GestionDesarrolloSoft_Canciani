import { useState } from 'react';

import { TablaCarreras } from '@/features/admin/components/TablaCarreras';
import { TablaCohortes } from '@/features/admin/components/TablaCohortes';
import { TablaMaterias } from '@/features/admin/components/TablaMaterias';
import { useCarreras, useMutateCarrera } from '@/features/admin/hooks/useCarreras';
import { useCohortes, useMutateCohorte } from '@/features/admin/hooks/useCohortes';
import { useMaterias, useMutateMateria } from '@/features/admin/hooks/useMaterias';
import { Alert } from '@/shared/components/ui/Alert';
import { Spinner } from '@/shared/components/ui/Spinner';

type TabKey = 'carreras' | 'cohortes' | 'materias';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'carreras', label: 'Carreras' },
  { key: 'cohortes', label: 'Cohortes' },
  { key: 'materias', label: 'Materias' },
];

export function EstructuraAcademicaPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('carreras');
  const [selectedCarreraId, setSelectedCarreraId] = useState('');

  const { data: carreras, isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes, isLoading: loadingCohortes } = useCohortes(selectedCarreraId || undefined);
  const { data: materias, isLoading: loadingMaterias } = useMaterias();

  const carreraMutate = useMutateCarrera();
  const cohorteMutate = useMutateCohorte();
  const materiaMutate = useMutateMateria();

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Estructura Académica</h1>
        <p className="mt-1 text-sm text-secondary-500">Gestión de carreras, cohortes y materias</p>
      </div>

      {errorMsg && <Alert variant="error">{errorMsg}</Alert>}
      {successMsg && <Alert variant="success">{successMsg}</Alert>}

      <div className="flex gap-2 border-b border-secondary-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'border-b-2 border-primary-600 text-primary-700'
                : 'text-secondary-500 hover:text-secondary-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'carreras' && (
        loadingCarreras ? <Spinner size="lg" /> : (
          <TablaCarreras
            carreras={carreras ?? []}
            isLoading={false}
            onSave={async (data) => {
              setErrorMsg(null); setSuccessMsg(null);
              try { await carreraMutate.create.mutateAsync(data); setSuccessMsg('Carrera creada'); }
              catch { setErrorMsg('Error al crear carrera'); }
            }}
            onToggleEstado={async (id) => {
              try { await carreraMutate.toggleEstado.mutateAsync(id); }
              catch { setErrorMsg('Error al cambiar estado'); }
            }}
            isSaving={carreraMutate.create.isPending}
          />
        )
      )}

      {activeTab === 'cohortes' && (
        <TablaCohortes
          cohortes={cohortes ?? []}
          carreras={carreras ?? []}
          isLoading={loadingCohortes}
          onSave={async (data) => {
            setErrorMsg(null); setSuccessMsg(null);
            try { await cohorteMutate.create.mutateAsync(data); setSuccessMsg('Cohorte creada'); }
            catch { setErrorMsg('Error al crear cohorte'); }
          }}
          onToggleEstado={async (id) => {
            try { await cohorteMutate.toggleEstado.mutateAsync(id); }
            catch { setErrorMsg('Error al cambiar estado'); }
          }}
          isSaving={cohorteMutate.create.isPending}
          selectedCarreraId={selectedCarreraId}
          onCarreraChange={setSelectedCarreraId}
        />
      )}

      {activeTab === 'materias' && (
        loadingMaterias ? <Spinner size="lg" /> : (
          <TablaMaterias
            materias={materias ?? []}
            carreras={carreras ?? []}
            isLoading={false}
            onSave={async (data, id) => {
              setErrorMsg(null); setSuccessMsg(null);
              try {
                if (id) {
                  await materiaMutate.update.mutateAsync({ id, payload: data });
                  setSuccessMsg('Materia actualizada');
                } else {
                  await materiaMutate.create.mutateAsync(data);
                  setSuccessMsg('Materia creada');
                }
              }
              catch { setErrorMsg('Error al guardar materia'); }
            }}
            onToggleEstado={async (id) => {
              try { await materiaMutate.toggleEstado.mutateAsync(id); }
              catch { setErrorMsg('Error al cambiar estado'); }
            }}
            isSaving={materiaMutate.create.isPending}
          />
        )
      )}
    </div>
  );
}
