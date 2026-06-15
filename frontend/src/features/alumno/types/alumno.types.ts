export interface MateriaEstado {
  materia_id: string;
  materia_nombre: string;
  carrera_nombre: string;
  cohorte_nombre: string;
  actividades_aprobadas: number;
  actividades_totales: number;
  porcentaje_aprobacion: number;
  estado: string; // "Regular" | "En riesgo"
}

export interface EstadoAcademico {
  materias: MateriaEstado[];
  resumen: {
    materias_totales: number;
    materias_regulares: number;
    materias_en_riesgo: number;
  };
}

export interface AvisoAlumno {
  id: string;
  titulo: string;
  created_at: string;
  acknowledged?: boolean;
}
