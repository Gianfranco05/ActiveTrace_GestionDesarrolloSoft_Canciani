import { clsx } from 'clsx';
import { Link } from 'react-router-dom';

import { Card } from '@/shared/components/ui/Card';

const modules = [
  { title: 'Equipos', desc: 'Gestioná equipos docentes, asignaciones y vigencias', path: '/coordinacion/equipos', color: 'bg-blue-500' },
  { title: 'Avisos', desc: 'Creá y gestioná avisos para el tenant', path: '/coordinacion/avisos', color: 'bg-amber-500' },
  { title: 'Tareas', desc: 'Administrá tareas internas del equipo', path: '/coordinacion/tareas', color: 'bg-green-500' },
  { title: 'Encuentros', desc: 'Programá encuentros y gestioná instancias', path: '/coordinacion/encuentros', color: 'bg-purple-500' },
  { title: 'Coloquios', desc: 'Administrá coloquios, reservas y notas', path: '/coordinacion/coloquios', color: 'bg-pink-500' },
  { title: 'Monitores', desc: 'Monitoreá actividades de alumnos', path: '/coordinacion/monitores', color: 'bg-teal-500' },
  { title: 'Setup', desc: 'Configuración de cuatrimestre', path: '/coordinacion/setup', color: 'bg-indigo-500' },
];

const kpis = [
  { label: 'Tareas Pendientes', value: '12', color: 'text-amber-600' },
  { label: 'Avisos Activos', value: '5', color: 'text-green-600' },
  { label: 'Próximos Encuentros', value: '8', color: 'text-blue-600' },
];

export function CoordinacionDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Panel de Coordinación</h1>
        <p className="mt-1 text-sm text-secondary-500">Bienvenido al panel de gestión académica</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {kpis.map((kpi) => (
          <Card key={kpi.label}>
            <div className="text-center">
              <p className="text-3xl font-bold text-secondary-900">{kpi.value}</p>
              <p className={clsx('mt-1 text-sm font-medium', kpi.color)}>{kpi.label}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map((mod) => (
          <Link key={mod.path} to={mod.path}>
            <Card className="h-full transition-shadow hover:shadow-lg">
              <div className="flex items-start gap-4">
                <div className={clsx('flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg', mod.color)}>
                  <span className="text-lg font-bold text-white">{mod.title[0]}</span>
                </div>
                <div>
                  <h3 className="font-semibold text-secondary-900">{mod.title}</h3>
                  <p className="mt-1 text-sm text-secondary-500">{mod.desc}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
