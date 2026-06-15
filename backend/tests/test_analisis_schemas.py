"""TDD: Analisis schemas — verify serialization, extra fields rejected."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.analisis import (
    AlumnoAtrasado,
    AtrasadosResponse,
    MonitorCoordinacionRow,
    MonitorGeneralRow,
    MonitorSeguimientoRow,
    NotaFinalRow,
    NotasFinalesResponse,
    RankingResponse,
    RankingRow,
    ReporteMateria,
    TPSinCorregirRow,
)


class TestAlumnoAtrasado:
    def test_valid(self):
        d = {
            "entrada_padron_id": uuid4(),
            "nombre": "Juan",
            "apellidos": "Perez",
            "email": "juan@test.com",
            "comision": "A",
            "motivo": "actividades_faltantes",
            "actividades_faltantes": ["TP1"],
            "actividades_reprobadas": [],
        }
        s = AlumnoAtrasado(**d)
        assert s.nombre == "Juan"
        assert s.motivo == "actividades_faltantes"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            AlumnoAtrasado(
                entrada_padron_id=uuid4(),
                nombre="Juan",
                apellidos="Perez",
                motivo="faltantes",
                actividades_faltantes=[],
                actividades_reprobadas=[],
                extra="no",
            )

    def test_defaults(self):
        d = {
            "entrada_padron_id": uuid4(),
            "nombre": "Juan",
            "apellidos": "Perez",
            "motivo": "nota_baja",
            "actividades_faltantes": [],
            "actividades_reprobadas": ["TP1"],
        }
        s = AlumnoAtrasado(**d)
        assert s.email is None
        assert s.comision is None


class TestAtrasadosResponse:
    def test_valid(self):
        item = {
            "entrada_padron_id": uuid4(),
            "nombre": "Juan",
            "apellidos": "Perez",
            "motivo": "faltantes",
            "actividades_faltantes": [],
            "actividades_reprobadas": [],
        }
        r = AtrasadosResponse(items=[AlumnoAtrasado(**item)], total=1, sin_datos=True)
        assert r.total == 1
        assert r.sin_datos is True


class TestRankingRow:
    def test_valid(self):
        d = {
            "posicion": 1,
            "entrada_padron_id": uuid4(),
            "nombre": "Ana",
            "apellidos": "Lopez",
            "aprobadas": 5,
            "total_actividades": 10,
            "porcentaje": Decimal("50.00"),
        }
        s = RankingRow(**d)
        assert s.posicion == 1

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            RankingRow(
                posicion=1,
                entrada_padron_id=uuid4(),
                nombre="A",
                apellidos="B",
                aprobadas=1,
                total_actividades=1,
                porcentaje=Decimal("100"),
                extra="x",
            )


class TestRankingResponse:
    def test_valid(self):
        row = {
            "posicion": 1,
            "entrada_padron_id": uuid4(),
            "nombre": "A",
            "apellidos": "B",
            "aprobadas": 3,
            "total_actividades": 5,
            "porcentaje": Decimal("60.00"),
        }
        r = RankingResponse(items=[RankingRow(**row)], total_aprobados=1)
        assert r.total_aprobados == 1


class TestNotaFinalRow:
    def test_valid(self):
        d = {
            "entrada_padron_id": uuid4(),
            "nombre": "Ana",
            "apellidos": "Lopez",
            "nota_promedio": Decimal("80.00"),
            "actividades_aprobadas": 3,
            "total_actividades": 5,
            "estado": "Regular",
        }
        s = NotaFinalRow(**d)
        assert s.nota_promedio == Decimal("80.00")

    def test_nota_promedio_null(self):
        d = {
            "entrada_padron_id": uuid4(),
            "nombre": "Ana",
            "apellidos": "Lopez",
            "nota_promedio": None,
            "actividades_aprobadas": 0,
            "total_actividades": 5,
            "estado": "Sin datos",
        }
        s = NotaFinalRow(**d)
        assert s.nota_promedio is None


class TestNotasFinalesResponse:
    def test_valid(self):
        row = {
            "entrada_padron_id": uuid4(),
            "nombre": "A",
            "apellidos": "B",
            "nota_promedio": None,
            "actividades_aprobadas": 0,
            "total_actividades": 5,
            "estado": "Sin datos",
        }
        r = NotasFinalesResponse(items=[NotaFinalRow(**row)])
        assert len(r.items) == 1


class TestReporteMateria:
    def test_valid(self):
        d = {
            "materia_id": uuid4(),
            "materia_nombre": "Matematica",
            "cohorte_id": uuid4(),
            "cohorte_nombre": "2026",
            "total_alumnos": 30,
            "alumnos_con_nota": 25,
            "alumnos_aprobados": 18,
            "alumnos_atrasados": 7,
            "pct_aprobados": Decimal("60.00"),
            "pct_atrasados": Decimal("23.33"),
            "actividades_count": 5,
        }
        s = ReporteMateria(**d)
        assert s.total_alumnos == 30

    def test_with_ultima_importacion(self):
        ts = datetime.now(timezone.utc)
        d = {
            "materia_id": uuid4(),
            "materia_nombre": "M",
            "cohorte_id": uuid4(),
            "cohorte_nombre": "C",
            "total_alumnos": 10,
            "alumnos_con_nota": 5,
            "alumnos_aprobados": 3,
            "alumnos_atrasados": 2,
            "pct_aprobados": Decimal("30.00"),
            "pct_atrasados": Decimal("20.00"),
            "actividades_count": 3,
            "ultima_importacion": ts,
        }
        s = ReporteMateria(**d)
        assert s.ultima_importacion == ts

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            ReporteMateria(
                materia_id=uuid4(),
                materia_nombre="M",
                cohorte_id=uuid4(),
                cohorte_nombre="C",
                total_alumnos=1,
                alumnos_con_nota=0,
                alumnos_aprobados=0,
                alumnos_atrasados=1,
                pct_aprobados=Decimal("0"),
                pct_atrasados=Decimal("100"),
                actividades_count=1,
                extra="x",
            )


class TestTPSinCorregirRow:
    def test_valid(self):
        d = {
            "actividad": "TP Escrito",
            "entrada_padron_id": uuid4(),
            "nombre": "Ana",
            "apellidos": "Lopez",
            "email": "ana@test.com",
            "comision": "A",
        }
        s = TPSinCorregirRow(**d)
        assert s.actividad == "TP Escrito"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TPSinCorregirRow(
                actividad="TP",
                entrada_padron_id=uuid4(),
                nombre="A",
                apellidos="B",
                extra="x",
            )


class TestMonitorGeneralRow:
    def test_valid(self):
        d = {
            "materia_id": uuid4(),
            "materia_nombre": "Matematica",
            "cohorte_id": uuid4(),
            "cohorte_nombre": "2026",
            "total_alumnos": 30,
            "aprobados": 18,
            "atrasados": 7,
            "pct_aprobacion": Decimal("60.00"),
        }
        s = MonitorGeneralRow(**d)
        assert s.aprobados == 18

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            MonitorGeneralRow(
                materia_id=uuid4(),
                materia_nombre="M",
                cohorte_id=uuid4(),
                cohorte_nombre="C",
                total_alumnos=1,
                aprobados=0,
                atrasados=1,
                pct_aprobacion=Decimal("0"),
                extra="x",
            )


class TestMonitorSeguimientoRow:
    def test_valid(self):
        d = {
            "entrada_padron_id": uuid4(),
            "nombre": "Ana",
            "apellidos": "Lopez",
            "email": "ana@test.com",
            "comision": "A",
            "actividades_aprobadas": 5,
            "actividades_reprobadas": 2,
            "actividades_faltantes": 1,
            "nota_promedio": Decimal("75.00"),
            "estado": "Al día",
        }
        s = MonitorSeguimientoRow(**d)
        assert s.estado == "Al día"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            MonitorSeguimientoRow(
                entrada_padron_id=uuid4(),
                nombre="A",
                apellidos="B",
                actividades_aprobadas=0,
                actividades_reprobadas=0,
                actividades_faltantes=0,
                estado="Sin datos",
                extra="x",
            )


class TestMonitorCoordinacionRow:
    def test_valid(self):
        d = {
            "materia_id": uuid4(),
            "materia_nombre": "Matematica",
            "cohorte_id": uuid4(),
            "cohorte_nombre": "2026",
            "total_alumnos": 30,
            "aprobados": 18,
            "atrasados": 7,
            "pct_aprobacion": Decimal("60.00"),
        }
        s = MonitorCoordinacionRow(**d)
        assert s.aprobados == 18

    def test_with_period(self):
        ts = datetime.now(timezone.utc)
        d = {
            "materia_id": uuid4(),
            "materia_nombre": "M",
            "cohorte_id": uuid4(),
            "cohorte_nombre": "C",
            "total_alumnos": 10,
            "aprobados": 5,
            "atrasados": 2,
            "pct_aprobacion": Decimal("50.00"),
            "period_desde": ts,
            "period_hasta": ts,
        }
        s = MonitorCoordinacionRow(**d)
        assert s.period_desde == ts
        assert s.period_hasta == ts

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            MonitorCoordinacionRow(
                materia_id=uuid4(),
                materia_nombre="M",
                cohorte_id=uuid4(),
                cohorte_nombre="C",
                total_alumnos=1,
                aprobados=0,
                atrasados=1,
                pct_aprobacion=Decimal("0"),
                extra="x",
            )
