import uuid
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.evaluaciones import (
    CupoPorDia,
    EvaluacionCreateRequest,
    EvaluacionUpdateRequest,
    ImportarAlumnosRequest,
    EvaluacionResponse,
    EvaluacionDetailResponse,
    ReservaRequest,
    ReservaResponse,
    ResultadoRequest,
    ResultadoResponse,
    PanelMetricasResponse,
    ConvocatoriaMetricasResponse,
)


class TestCupoPorDia:
    def test_valid(self):
        c = CupoPorDia(fecha=date(2026, 6, 15), cupo=5)
        assert c.fecha == date(2026, 6, 15)
        assert c.cupo == 5

    def test_rejects_negative_cupo(self):
        with pytest.raises(ValidationError):
            CupoPorDia(fecha=date(2026, 6, 15), cupo=0)

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            CupoPorDia(fecha=date(2026, 6, 15), cupo=5, extra="nope")


class TestEvaluacionCreateRequest:
    def test_valid(self):
        r = EvaluacionCreateRequest(
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            tipo="Coloquio",
            instancia="Primer cuatrimestre",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 6, 15), cupo=5)],
        )
        assert r.tipo == "Coloquio"
        assert len(r.cupos_por_dia) == 1

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            EvaluacionCreateRequest(
                materia_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                tipo="Coloquio",
                instancia="Test",
                cupos_por_dia=[CupoPorDia(fecha=date(2026, 6, 15), cupo=5)],
                extra="nope",
            )

    def test_rejects_empty_cupos(self):
        with pytest.raises(ValidationError):
            EvaluacionCreateRequest(
                materia_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                tipo="Coloquio",
                instancia="Test",
                cupos_por_dia=[],
            )

    def test_rejects_invalid_tipo(self):
        with pytest.raises(ValidationError):
            EvaluacionCreateRequest(
                materia_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                tipo="InvalidTipo",
                instancia="Test",
                cupos_por_dia=[CupoPorDia(fecha=date(2026, 6, 15), cupo=5)],
            )


class TestEvaluacionUpdateRequest:
    def test_partial_update(self):
        r = EvaluacionUpdateRequest(instancia="Nueva instancia")
        assert r.instancia == "Nueva instancia"
        assert r.cupos_por_dia is None
        assert r.activa is None

    def test_full_update(self):
        r = EvaluacionUpdateRequest(
            instancia="Nueva",
            cupos_por_dia=[CupoPorDia(fecha=date(2026, 7, 1), cupo=10)],
            activa=False,
        )
        assert r.activa is False


class TestImportarAlumnosRequest:
    def test_manual_valid(self):
        r = ImportarAlumnosRequest(
            modo="manual",
            usuario_ids=[uuid.uuid4(), uuid.uuid4()],
        )
        assert r.modo == "manual"
        assert len(r.usuario_ids) == 2

    def test_padron_valid(self):
        r = ImportarAlumnosRequest(
            modo="padron",
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
        )
        assert r.modo == "padron"

    def test_invalid_modo(self):
        with pytest.raises(ValidationError):
            ImportarAlumnosRequest(modo="invalid")


class TestReservaRequest:
    def test_requires_fecha_hora(self):
        with pytest.raises(ValidationError):
            ReservaRequest()

    def test_valid(self):
        r = ReservaRequest(fecha_hora=datetime(2026, 6, 15, 14, 0))
        assert r.fecha_hora is not None


class TestResultadoRequest:
    def test_requires_nota_final(self):
        with pytest.raises(ValidationError):
            ResultadoRequest(alumno_id=uuid.uuid4())

    def test_valid(self):
        r = ResultadoRequest(alumno_id=uuid.uuid4(), nota_final="8.0")
        assert r.nota_final == "8.0"


class TestEvaluacionResponse:
    def test_includes_metrics(self):
        r = EvaluacionResponse(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            materia_nombre="Matematica",
            cohorte_id=uuid.uuid4(),
            cohorte_nombre="2026-A",
            tipo="Coloquio",
            instancia="Final",
            cupos_por_dia=[{"fecha": "2026-06-15", "cupo": 5}],
            activa=True,
            total_convocados=10,
            total_reservas=5,
            total_resultados=3,
            cupos_libres=2,
        )
        assert r.total_convocados == 10
        assert r.cupos_libres == 2


class TestPanelMetricasResponse:
    def test_with_data(self):
        r = PanelMetricasResponse(
            total_convocatorias_activas=3,
            total_convocados=30,
            total_reservas_activas=15,
            total_resultados=10,
            tasa_aprobacion=0.8,
        )
        assert r.tasa_aprobacion == 0.8

    def test_tasa_none_when_no_data(self):
        r = PanelMetricasResponse(
            total_convocatorias_activas=0,
            total_convocados=0,
            total_reservas_activas=0,
            total_resultados=0,
            tasa_aprobacion=None,
        )
        assert r.tasa_aprobacion is None
