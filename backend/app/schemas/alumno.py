from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MateriaEstadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    materia_id: UUID
    materia_nombre: str
    carrera_nombre: str
    cohorte_nombre: str
    actividades_aprobadas: int
    actividades_totales: int
    porcentaje_aprobacion: float
    estado: str


class EstadoAcademicoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materias: list[MateriaEstadoResponse]
    resumen: dict
