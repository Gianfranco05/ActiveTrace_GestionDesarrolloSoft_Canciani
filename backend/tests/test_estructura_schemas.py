import uuid
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.estructura import (
    CarreraCreate,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    EstructuraListResponse,
    MateriaCreate,
    MateriaResponse,
    MateriaUpdate,
)


class TestCarreraSchemas:
    def test_carrera_create_valid(self):
        data = CarreraCreate(codigo="PROG", nombre="Programación")
        assert data.codigo == "PROG"
        assert data.nombre == "Programación"
        assert data.estado is None

    def test_carrera_create_with_estado(self):
        data = CarreraCreate(codigo="PROG", nombre="Prog", estado="Inactiva")
        assert data.estado == "Inactiva"

    def test_carrera_create_extra_forbid(self):
        with pytest.raises(ValidationError):
            CarreraCreate(codigo="X", nombre="X", extra_field="bad")

    def test_carrera_update_all_optional(self):
        data = CarreraUpdate()
        assert data.codigo is None
        assert data.nombre is None
        assert data.estado is None

    def test_carrera_update_partial(self):
        data = CarreraUpdate(nombre="Nuevo Nombre")
        assert data.nombre == "Nuevo Nombre"
        assert data.codigo is None

    def test_carrera_response_from_attributes(self):
        now = datetime.now(timezone.utc)
        data = CarreraResponse(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            codigo="PROG",
            nombre="Programación",
            estado="Activa",
            created_at=now,
            updated_at=now,
        )
        assert data.codigo == "PROG"
        assert data.estado == "Activa"


class TestCohorteSchemas:
    def test_cohorte_create_valid(self):
        data = CohorteCreate(
            carrera_id=uuid.uuid4(),
            nombre="AGO-2025",
            anio=2025,
            vig_desde=date(2025, 8, 1),
        )
        assert data.nombre == "AGO-2025"
        assert data.vig_hasta is None

    def test_cohorte_create_with_vig_hasta(self):
        data = CohorteCreate(
            carrera_id=uuid.uuid4(),
            nombre="MAR-2025",
            anio=2025,
            vig_desde=date(2025, 3, 1),
            vig_hasta=date(2025, 12, 31),
        )
        assert data.vig_hasta == date(2025, 12, 31)

    def test_cohorte_create_extra_forbid(self):
        with pytest.raises(ValidationError):
            CohorteCreate(
                carrera_id=uuid.uuid4(),
                nombre="X", anio=2025,
                vig_desde=date.today(),
                extra="bad",
            )


class TestMateriaSchemas:
    def test_materia_create_valid(self):
        data = MateriaCreate(codigo="MATE_I", nombre="Matemática I")
        assert data.codigo == "MATE_I"

    def test_materia_update_partial(self):
        data = MateriaUpdate(estado="Inactiva")
        assert data.estado == "Inactiva"
        assert data.codigo is None

    def test_materia_response_from_attributes(self):
        now = datetime.now(timezone.utc)
        data = MateriaResponse(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            codigo="FISICA",
            nombre="Física",
            estado="Activa",
            created_at=now,
            updated_at=now,
        )
        assert data.codigo == "FISICA"


class TestEstructuraListResponse:
    def test_list_response(self):
        data = EstructuraListResponse(items=[], total=0)
        assert data.items == []
        assert data.total == 0
        assert data.offset == 0
        assert data.limit == 100

    def test_list_response_with_items(self):
        items = [{"id": "1"}, {"id": "2"}]
        data = EstructuraListResponse(items=items, total=2, offset=0, limit=10)
        assert data.total == 2
        assert data.limit == 10
