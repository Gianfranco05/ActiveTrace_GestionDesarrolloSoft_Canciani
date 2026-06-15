import uuid
from datetime import date, datetime, time
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiaSemana(StrEnum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class EstadoEncuentro(StrEnum):
    PROGRAMADO = "Programado"
    REALIZADO = "Realizado"
    CANCELADO = "Cancelado"


class SlotRecurrenteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    asignacion_id: uuid.UUID | None = None
    titulo: str = Field(default="", max_length=200)
    hora: time | None = None
    horario: str | None = None
    dia_semana: int | DiaSemana = 1  # 0=Domingo..6=Sábado, o enum DiaSemana
    fecha_inicio: date
    cant_semanas: int = Field(default=12, ge=1, le=52)
    semanas: int | None = Field(default=None, ge=1, le=52)
    meet_url: str | None = Field(default=None, max_length=500)
    enlace: str | None = Field(default=None, max_length=500)

    _INT_TO_DIA: dict[int, DiaSemana] = {
        0: DiaSemana.DOMINGO, 1: DiaSemana.LUNES, 2: DiaSemana.MARTES,
        3: DiaSemana.MIERCOLES, 4: DiaSemana.JUEVES, 5: DiaSemana.VIERNES,
        6: DiaSemana.SABADO,
    }

    @model_validator(mode="after")
    def _normalize_fields(self):
        # Normalize dia_semana: int → DiaSemana
        if isinstance(self.dia_semana, int):
            if self.dia_semana not in self._INT_TO_DIA:
                raise ValueError(f"Día de semana inválido: {self.dia_semana}. Usá 0-6 o el nombre del día.")
            self.dia_semana = self._INT_TO_DIA[self.dia_semana]

        # Copy enlace → meet_url
        if self.enlace and not self.meet_url:
            self.meet_url = self.enlace

        # Parse horario → hora
        if self.horario and not self.hora:
            try:
                parts = self.horario.strip().split(":")
                self.hora = time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                raise ValueError(f"Formato de horario inválido: '{self.horario}'. Usá HH:MM (ej: 14:30)")

        if self.hora is None:
            raise ValueError("El campo 'horario' es obligatorio (formato HH:MM, ej: 14:30)")

        return self


class SlotUnicoCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    asignacion_id: uuid.UUID
    titulo: str = Field(max_length=200)
    hora: time
    fecha_unica: date
    meet_url: str | None = Field(default=None, max_length=500)


class InstanciaEncuentroResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    slot_id: uuid.UUID | None
    materia_id: uuid.UUID
    fecha: date
    hora: time
    titulo: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    created_at: datetime
    updated_at: datetime


class SlotEncuentroResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    materia_id: uuid.UUID
    asignacion_id: uuid.UUID
    titulo: str
    hora: time
    dia_semana: str | None = None
    fecha_inicio: date | None = None
    cant_semanas: int | None = None
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None
    instancias: list[InstanciaEncuentroResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class InstanciaUnicaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    asignacion_id: uuid.UUID | None = None
    titulo: str = Field(default="", max_length=200)
    fecha: date
    hora: time | None = None
    horario: str | None = None
    meet_url: str | None = Field(default=None, max_length=500)
    enlace: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _normalize_fields(self):
        # Copy enlace → meet_url
        if self.enlace and not self.meet_url:
            self.meet_url = self.enlace

        # Parse horario → hora
        if self.horario and not self.hora:
            try:
                parts = self.horario.strip().split(":")
                self.hora = time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                raise ValueError(f"Formato de horario inválido: '{self.horario}'. Usá HH:MM (ej: 14:30)")

        # hora is required by DB — validate it's set
        if self.hora is None:
            raise ValueError("El campo 'horario' es obligatorio (formato HH:MM, ej: 14:30)")

        return self


class InstanciaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoEncuentro | None = None
    meet_url: str | None = Field(default=None, max_length=500)
    video_url: str | None = Field(default=None, max_length=500)
    comentario: str | None = None


class HtmlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    html: str


class EncuentrosListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list
    total: int
    offset: int = 0
    limit: int = 20


class EncuentroItemResponse(BaseModel):
    """Unified response matching frontend Encuentro type."""
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    materia_id: uuid.UUID
    materia_nombre: str = ""
    docente_id: uuid.UUID | None = None
    docente_nombre: str = ""
    fecha: date | None = None
    horario: str = ""
    titulo: str = ""
    enlace: str | None = None
    grabacion: str | None = None
    estado: str = "programado"
    comentario: str | None = None
    es_recurrente: bool = False
    created_at: datetime | None = None


class EncuentroListResponse(BaseModel):
    """Paginated response for frontend."""
    data: list[EncuentroItemResponse]
    total: int
    page: int
    total_pages: int
