"""TDD: Equipo schemas — serialization and validation."""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.asignaciones import (
    EquipoResponse,
    EquipoDetailResponse,
    AsignacionMasivaRequest,
    ClonarRequest,
    VigenciaUpdateRequest,
    UsuarioSearchResponse,
    AsignacionResponse,
)


class TestEquipoResponse:
    def test_valid_equipo_response(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "materia_nombre": "Matemática",
            "carrera_nombre": "TUPAD",
            "cohorte_nombre": "AGO-2025",
            "total_asignaciones": 5,
        }
        resp = EquipoResponse(**data)
        assert resp.materia_nombre == "Matemática"
        assert resp.total_asignaciones == 5

    def test_extra_fields_rejected(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "materia_nombre": "M",
            "carrera_nombre": "C",
            "cohorte_nombre": "Ch",
            "total_asignaciones": 1,
            "extra": "should_fail",
        }
        with pytest.raises(ValidationError):
            EquipoResponse(**data)


class TestEquipoDetailResponse:
    def test_valid_detail_response(self):
        asig = AsignacionResponse(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            rol_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            comisiones=None,
            responsable_id=None,
            vig_desde=date(2025, 1, 1),
            vig_hasta=None,
            estado_vigencia="Vigente",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "asignaciones": [asig],
        }
        resp = EquipoDetailResponse(**data)
        assert len(resp.asignaciones) == 1
        assert resp.asignaciones[0].estado_vigencia == "Vigente"

    def test_extra_fields_rejected(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "asignaciones": [],
            "extra": "bad",
        }
        with pytest.raises(ValidationError):
            EquipoDetailResponse(**data)


class TestAsignacionMasivaRequest:
    def test_valid_request(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "rol_id": uuid.uuid4(),
            "usuario_ids": [uuid.uuid4()],
            "vig_desde": date(2025, 1, 1),
        }
        req = AsignacionMasivaRequest(**data)
        assert len(req.usuario_ids) == 1

    def test_rejects_more_than_100(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "rol_id": uuid.uuid4(),
            "usuario_ids": [uuid.uuid4() for _ in range(101)],
            "vig_desde": date(2025, 1, 1),
        }
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(**data)

    def test_rejects_empty_usuario_ids(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "rol_id": uuid.uuid4(),
            "usuario_ids": [],
            "vig_desde": date(2025, 1, 1),
        }
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(**data)

    def test_extra_fields_rejected(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "rol_id": uuid.uuid4(),
            "usuario_ids": [uuid.uuid4()],
            "vig_desde": date(2025, 1, 1),
            "extra": "bad",
        }
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(**data)

    def test_accepts_optional_fields(self):
        data = {
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "rol_id": uuid.uuid4(),
            "usuario_ids": [uuid.uuid4()],
            "vig_desde": date(2025, 1, 1),
            "vig_hasta": date(2025, 12, 31),
            "comisiones": "A,B,C",
        }
        req = AsignacionMasivaRequest(**data)
        assert req.vig_hasta == date(2025, 12, 31)
        assert req.comisiones == "A,B,C"


class TestClonarRequest:
    def test_valid_request(self):
        data = {
            "origen_materia_id": uuid.uuid4(),
            "origen_carrera_id": uuid.uuid4(),
            "origen_cohorte_id": uuid.uuid4(),
            "destino_materia_id": uuid.uuid4(),
            "destino_carrera_id": uuid.uuid4(),
            "destino_cohorte_id": uuid.uuid4(),
            "nueva_vig_desde": date(2025, 1, 1),
        }
        req = ClonarRequest(**data)
        assert req.origen_materia_id is not None
        assert req.destino_materia_id is not None

    def test_extra_fields_rejected(self):
        data = {
            "origen_materia_id": uuid.uuid4(),
            "origen_carrera_id": uuid.uuid4(),
            "origen_cohorte_id": uuid.uuid4(),
            "destino_materia_id": uuid.uuid4(),
            "destino_carrera_id": uuid.uuid4(),
            "destino_cohorte_id": uuid.uuid4(),
            "nueva_vig_desde": date(2025, 1, 1),
            "extra": "bad",
        }
        with pytest.raises(ValidationError):
            ClonarRequest(**data)


class TestVigenciaUpdateRequest:
    def test_valid_request(self):
        data = {"vig_desde": date(2025, 1, 1)}
        req = VigenciaUpdateRequest(**data)
        assert req.vig_desde == date(2025, 1, 1)

    def test_with_vig_hasta(self):
        data = {"vig_desde": date(2025, 1, 1), "vig_hasta": date(2025, 12, 31)}
        req = VigenciaUpdateRequest(**data)
        assert req.vig_hasta == date(2025, 12, 31)

    def test_extra_fields_rejected(self):
        data = {"vig_desde": date(2025, 1, 1), "extra": "bad"}
        with pytest.raises(ValidationError):
            VigenciaUpdateRequest(**data)


class TestUsuarioSearchResponse:
    def test_valid_response(self):
        data = {
            "id": uuid.uuid4(),
            "nombre": "Martín",
            "apellidos": "García",
            "legajo": "LEG-001",
        }
        resp = UsuarioSearchResponse(**data)
        assert resp.nombre == "Martín"

    def test_legajo_optional(self):
        data = {
            "id": uuid.uuid4(),
            "nombre": "Laura",
            "apellidos": "Pérez",
        }
        resp = UsuarioSearchResponse(**data)
        assert resp.legajo is None

    def test_extra_fields_rejected(self):
        data = {
            "id": uuid.uuid4(),
            "nombre": "N",
            "apellidos": "A",
            "extra": "bad",
        }
        with pytest.raises(ValidationError):
            UsuarioSearchResponse(**data)
