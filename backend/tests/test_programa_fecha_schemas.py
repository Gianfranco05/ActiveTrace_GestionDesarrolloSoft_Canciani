import uuid
from datetime import date, datetime

import pytest
from pydantic import ValidationError


class TestProgramaMateriaSchema:
    def test_create_request_required_fields(self):
        from app.schemas.programas import ProgramaMateriaCreateRequest

        data = {
            "materia_id": str(uuid.uuid4()),
            "carrera_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "titulo": "Programa Analitico",
        }
        schema = ProgramaMateriaCreateRequest(**data)
        assert schema.titulo == "Programa Analitico"

    def test_create_request_rejects_missing_required(self):
        from app.schemas.programas import ProgramaMateriaCreateRequest

        with pytest.raises(ValidationError):
            ProgramaMateriaCreateRequest(
                materia_id=str(uuid.uuid4()),
                carrera_id=str(uuid.uuid4()),
                cohorte_id=str(uuid.uuid4()),
            )

    def test_create_request_rejects_extra_fields(self):
        from app.schemas.programas import ProgramaMateriaCreateRequest

        with pytest.raises(ValidationError):
            ProgramaMateriaCreateRequest(
                materia_id=str(uuid.uuid4()),
                carrera_id=str(uuid.uuid4()),
                cohorte_id=str(uuid.uuid4()),
                titulo="Test",
                extra_field="should not be here",
            )

    def test_response_from_attributes(self):
        from app.schemas.programas import ProgramaMateriaResponse

        data = {
            "id": uuid.uuid4(),
            "materia_id": uuid.uuid4(),
            "carrera_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "titulo": "Test Program",
            "referencia_archivo": "s3://bucket/test.pdf",
            "cargado_at": datetime(2026, 4, 15, 10, 30),
        }
        response = ProgramaMateriaResponse(**data)
        assert response.id == data["id"]
        assert response.titulo == "Test Program"
        assert response.referencia_archivo == "s3://bucket/test.pdf"


class TestFechaAcademicaSchema:
    def test_create_request_valid(self):
        from app.schemas.fechas_academicas import FechaAcademicaCreateRequest

        data = {
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15",
            "titulo": "Primer Parcial",
        }
        schema = FechaAcademicaCreateRequest(**data)
        assert schema.tipo == "Parcial"
        assert schema.numero == 1

    def test_create_request_rejects_numero_zero(self):
        from app.schemas.fechas_academicas import FechaAcademicaCreateRequest

        with pytest.raises(ValidationError):
            FechaAcademicaCreateRequest(
                materia_id=str(uuid.uuid4()),
                cohorte_id=str(uuid.uuid4()),
                tipo="Parcial",
                numero=0,
                periodo="2026-1",
                fecha="2026-04-15",
            )

    def test_create_request_rejects_numero_negative(self):
        from app.schemas.fechas_academicas import FechaAcademicaCreateRequest

        with pytest.raises(ValidationError):
            FechaAcademicaCreateRequest(
                materia_id=str(uuid.uuid4()),
                cohorte_id=str(uuid.uuid4()),
                tipo="Parcial",
                numero=-1,
                periodo="2026-1",
                fecha="2026-04-15",
            )

    def test_create_request_titulo_optional(self):
        from app.schemas.fechas_academicas import FechaAcademicaCreateRequest

        schema = FechaAcademicaCreateRequest(
            materia_id=str(uuid.uuid4()),
            cohorte_id=str(uuid.uuid4()),
            tipo="Coloquio",
            numero=1,
            periodo="2026-1",
            fecha="2026-06-20",
        )
        assert schema.titulo is None

    def test_create_request_rejects_extra(self):
        from app.schemas.fechas_academicas import FechaAcademicaCreateRequest

        with pytest.raises(ValidationError):
            FechaAcademicaCreateRequest(
                materia_id=str(uuid.uuid4()),
                cohorte_id=str(uuid.uuid4()),
                tipo="Parcial",
                numero=1,
                periodo="2026-1",
                fecha="2026-04-15",
                no_deberia_estar_aqui="no",
            )

    def test_update_request_all_optional(self):
        from app.schemas.fechas_academicas import FechaAcademicaUpdateRequest

        schema = FechaAcademicaUpdateRequest()
        assert schema.tipo is None
        assert schema.numero is None
        assert schema.periodo is None
        assert schema.fecha is None
        assert schema.titulo is None

    def test_update_request_partial(self):
        from app.schemas.fechas_academicas import FechaAcademicaUpdateRequest

        schema = FechaAcademicaUpdateRequest(tipo="TP")
        assert schema.tipo == "TP"
        assert schema.numero is None

    def test_update_request_rejects_extra(self):
        from app.schemas.fechas_academicas import FechaAcademicaUpdateRequest

        with pytest.raises(ValidationError):
            FechaAcademicaUpdateRequest(extra="nope")

    def test_response_from_attributes(self):
        from app.schemas.fechas_academicas import FechaAcademicaResponse

        data = {
            "id": uuid.uuid4(),
            "materia_id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": date(2026, 4, 15),
            "titulo": "Primer Parcial",
        }
        response = FechaAcademicaResponse(**data)
        assert response.tipo == "Parcial"
        assert response.fecha == date(2026, 4, 15)

    def test_lms_html_response(self):
        from app.schemas.fechas_academicas import FechasLmsHtmlResponse

        data = {"html": "<div>table</div>"}
        response = FechasLmsHtmlResponse(**data)
        assert response.html == "<div>table</div>"

    def test_lms_html_response_rejects_extra(self):
        from app.schemas.fechas_academicas import FechasLmsHtmlResponse

        with pytest.raises(ValidationError):
            FechasLmsHtmlResponse(html="<div>test</div>", extra="no")
