import type { ComponentType, SVGProps } from 'react';

export interface NavItem {
  label: string;
  path: string;
  icon?: ComponentType<SVGProps<SVGSVGElement>>;
  permission: string | null;
  roles?: string[];
  children?: NavItem[];
}

export const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    permission: null,
  },
  {
    label: 'Académico',
    path: '/academico',
    permission: null,
    children: [
      {
        label: 'Importar Calificaciones',
        path: '/academico/importar',
        permission: 'calificaciones:importar',
      },
      {
        label: 'Configurar Umbral',
        path: '/academico/umbral',
        permission: 'calificaciones:importar',
      },
      {
        label: 'Atrasados',
        path: '/academico/atrasados',
        permission: 'atrasados:ver',
      },
      {
        label: 'Ranking',
        path: '/academico/ranking',
        permission: 'atrasados:ver',
      },
      {
        label: 'Notas Finales',
        path: '/academico/notas-finales',
        permission: 'atrasados:ver',
      },
      {
        label: 'Reportes',
        path: '/academico/reportes',
        permission: 'atrasados:ver',
      },
      {
        label: 'Entregas sin Corregir',
        path: '/academico/entregas',
        permission: 'atrasados:ver',
      },
      {
        label: 'Comunicaciones',
        path: '/academico/comunicaciones',
        permission: 'comunicacion:enviar',
      },
      {
        label: 'Monitores',
        path: '/academico/monitores',
        permission: 'atrasados:ver',
      },
    ],
  },
  {
    label: 'Coordinación',
    path: '/coordinacion',
    permission: null,
    children: [
      {
        label: 'Equipos Docentes',
        path: '/coordinacion/equipos',
        permission: 'equipos:asignar',
      },
      {
        label: 'Encuentros',
        path: '/coordinacion/encuentros',
        permission: 'encuentros:gestionar',
      },
      {
        label: 'Coloquios',
        path: '/coordinacion/coloquios',
        permission: 'coloquios:gestionar',
      },
      {
        label: 'Tareas',
        path: '/coordinacion/tareas',
        permission: 'tareas:gestionar',
      },
      {
        label: 'Avisos',
        path: '/coordinacion/avisos',
        permission: 'avisos:publicar',
      },
    ],
  },
  {
    label: 'Administración',
    path: '/admin',
    permission: null,
    roles: ['ADMIN'],
    children: [
      {
        label: 'Usuarios',
        path: '/admin/usuarios',
        permission: 'usuarios:gestionar',
      },
      {
        label: 'Estructura Académica',
        path: '/admin/estructura',
        permission: 'estructura:gestionar',
      },
      {
        label: 'Auditoría',
        path: '/admin/auditoria',
        permission: 'auditoria:ver',
      },
      {
        label: 'Log Auditoría',
        path: '/admin/auditoria/log',
        permission: 'auditoria:ver',
      },
    ],
  },
  {
    label: 'Alumno',
    path: '/alumno',
    permission: null,
    roles: ['ALUMNO'],
    children: [
      { label: 'Mi Estado', path: '/alumno/estado', permission: 'estado_academico:ver' },
      { label: 'Mis Avisos', path: '/alumno/avisos', permission: 'aviso:confirmar' },
      { label: 'Coloquios', path: '/alumno/coloquios', permission: 'coloquios:reservar' },
    ],
  },
  {
    label: 'Finanzas',
    path: '/finanzas',
    permission: null,
    children: [
      {
        label: 'Liquidaciones',
        path: '/finanzas/liquidaciones',
        permission: 'liquidaciones:ver',
      },
    ],
  },

  {
    label: 'Perfil',
    path: '/perfil',
    permission: 'perfil:editar',
  },
];
