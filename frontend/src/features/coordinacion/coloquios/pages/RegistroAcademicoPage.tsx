import { useRegistroAcademico } from '@/features/coordinacion/coloquios/hooks/useColoquios';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';

export function RegistroAcademicoPage() {
  const { data: registros, isLoading } = useRegistroAcademico();

  const columns: Column[] = [
    { key: 'alumno_nombre', header: 'Alumno' },
    { key: 'materia_nombre', header: 'Materia' },
    { key: 'instancia', header: 'Instancia' },
    { key: 'nota', header: 'Nota', render: (item) => item.nota ?? '—' },
    { key: 'fecha_registro', header: 'Fecha de Registro' },
  ];

  if (isLoading) {
    return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Registro Académico</h1>
      <Card>
        <DataTable columns={columns} data={registros ?? []} keyExtractor={(r) => r.id} />
      </Card>
    </div>
  );
}
