import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.avisos import (
    AvisoCreateRequest,
    AvisoUpdateRequest,
    AvisoResponse,
    AvisoListItemResponse,
    AlcanceEnum,
    SeveridadEnum,
)


class TestAvisoCreateRequest:
    def test_valid_create_request(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Bienvenida",
            "cuerpo": "Hola a todos",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        req = AvisoCreateRequest(**data)
        assert req.alcance == AlcanceEnum.Global
        assert req.activo is True
        assert req.requiere_ack is False
        assert req.orden == 0

    def test_rejects_extra_fields(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "campo_extra": "no permitido",
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_titulo_truncated_at_201_chars(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "A" * 201,
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_titulo_exactly_200_chars_ok(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "A" * 200,
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        req = AvisoCreateRequest(**data)
        assert len(req.titulo) == 200

    def test_alcance_required(self):
        data = {
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_inicio_en_required(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_fin_en_required(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_severidad_required(self):
        data = {
            "alcance": "Global",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_invalid_alcance(self):
        data = {
            "alcance": "InvalidScope",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_invalid_severidad(self):
        data = {
            "alcance": "Global",
            "severidad": "InvalidSeveridad",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        with pytest.raises(ValidationError):
            AvisoCreateRequest(**data)

    def test_optional_fields_default(self):
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        req = AvisoCreateRequest(**data)
        assert req.materia_id is None
        assert req.cohorte_id is None
        assert req.rol_destino is None

    def test_por_materia_with_materia_id(self):
        materia_id = uuid.uuid4()
        data = {
            "alcance": "PorMateria",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "materia_id": materia_id,
        }
        req = AvisoCreateRequest(**data)
        assert req.alcance == AlcanceEnum.PorMateria
        assert req.materia_id == materia_id

    def test_por_cohorte_with_cohorte_id(self):
        cohorte_id = uuid.uuid4()
        data = {
            "alcance": "PorCohorte",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "cohorte_id": cohorte_id,
        }
        req = AvisoCreateRequest(**data)
        assert req.alcance == AlcanceEnum.PorCohorte
        assert req.cohorte_id == cohorte_id

    def test_por_rol_with_rol_destino(self):
        data = {
            "alcance": "PorRol",
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "rol_destino": "PROFESOR",
        }
        req = AvisoCreateRequest(**data)
        assert req.alcance == AlcanceEnum.PorRol
        assert req.rol_destino == "PROFESOR"


class TestAvisoUpdateRequest:
    def test_all_fields_optional(self):
        req = AvisoUpdateRequest()
        assert req.titulo is None
        assert req.alcance is None

    def test_partial_update_only_titulo(self):
        req = AvisoUpdateRequest(titulo="Nuevo título")
        assert req.titulo == "Nuevo título"
        assert req.cuerpo is None

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            AvisoUpdateRequest(campo_extra="no")

    def test_titulo_max_200(self):
        req = AvisoUpdateRequest(titulo="A" * 200)
        assert len(req.titulo) == 200

    def test_titulo_over_200(self):
        with pytest.raises(ValidationError):
            AvisoUpdateRequest(titulo="A" * 201)


class TestAvisoResponse:
    def test_from_attributes(self):
        data = {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "alcance": "Global",
            "materia_id": None,
            "cohorte_id": None,
            "rol_destino": None,
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "orden": 0,
            "activo": True,
            "requiere_ack": False,
            "created_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
        resp = AvisoResponse(**data)
        assert resp.alcance == AlcanceEnum.Global
        assert resp.severidad == SeveridadEnum.Info
        assert resp.activo is True
        assert resp.requiere_ack is False
        assert resp.titulo == "Test"

    def test_extra_forbid(self):
        data = {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "alcance": "Global",
            "materia_id": None,
            "cohorte_id": None,
            "rol_destino": None,
            "severidad": "Info",
            "titulo": "Test",
            "cuerpo": "Body",
            "inicio_en": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "fin_en": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "orden": 0,
            "activo": True,
            "requiere_ack": False,
            "created_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "extra": "no permitido",
        }
        with pytest.raises(ValidationError):
            AvisoResponse(**data)
