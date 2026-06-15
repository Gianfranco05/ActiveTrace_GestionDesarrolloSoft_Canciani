import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProgramaMateriaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    titulo: str


class ProgramaMateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    titulo: str
    referencia_archivo: str
    cargado_at: datetime
