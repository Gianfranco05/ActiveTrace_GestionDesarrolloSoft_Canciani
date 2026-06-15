"""TDD 10.2: Pydantic schema tests for calificaciones."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.calificacion import (
    ActividadDetectada,
    CalificacionResponse,
    ImportPreviewResponse,
    ReporteAlumno,
    UmbralMateriaResponse,
    UmbralMateriaUpdate,
)


def test_calificacion_response_from_attrs():
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid4(),
        "materia_id": uuid4(),
        "cohorte_id": uuid4(),
        "entrada_padron_id": uuid4(),
        "actividad": "TP1",
        "tipo": "Numerica",
        "nota_numerica": 75.00,
        "nota_textual": None,
        "aprobado": True,
        "origen": "Importado",
        "importado_at": now,
    }
    resp = CalificacionResponse(**data)
    assert resp.actividad == "TP1"
    assert resp.aprobado is True
    assert resp.origen == "Importado"


def test_calificacion_response_extra_forbidden():
    with pytest.raises(ValidationError):
        CalificacionResponse(id=uuid4(), materia_id=uuid4(), cohorte_id=uuid4(),
                             entrada_padron_id=uuid4(), actividad="X", tipo="N",
                             aprobado=True, origen="I", importado_at=datetime.now(timezone.utc),
                             extra_field="should_fail")


def test_umbral_materia_response():
    data = {
        "materia_id": uuid4(),
        "asignacion_id": None,
        "umbral_pct": 60,
        "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"],
    }
    resp = UmbralMateriaResponse(**data)
    assert resp.umbral_pct == 60
    assert resp.asignacion_id is None


def test_umbral_materia_response_extra_forbidden():
    with pytest.raises(ValidationError):
        UmbralMateriaResponse(materia_id=uuid4(), umbral_pct=60,
                              valores_aprobatorios=["A"], extra="x")


def test_umbral_materia_update():
    resp = UmbralMateriaUpdate(umbral_pct=75)
    assert resp.umbral_pct == 75


def test_umbral_materia_update_extra_forbidden():
    with pytest.raises(ValidationError):
        UmbralMateriaUpdate(umbral_pct=60, extra="x")


def test_actividad_detectada():
    a = ActividadDetectada(header="TP1 (Real)", nombre="TP1", tipo="Numerica")
    assert a.header == "TP1 (Real)"
    assert a.nombre == "TP1"
    assert a.tipo == "Numerica"


def test_import_preview_response():
    data = {
        "filename": "test.xlsx",
        "total_rows": 100,
        "preview_rows": [{"nombre": "Ana"}],
        "actividades_detectadas": [
            {"header": "TP1 (Real)", "nombre": "TP1", "tipo": "Numerica"},
        ],
    }
    resp = ImportPreviewResponse(**data)
    assert resp.total_rows == 100
    assert len(resp.actividades_detectadas) == 1


def test_reporte_alumno():
    a = ReporteAlumno(nombre="Ana", apellidos="Lopez", email="ana@test.com")
    assert a.nombre == "Ana"
    assert a.email == "ana@test.com"


def test_reporte_alumno_no_email():
    a = ReporteAlumno(nombre="Ana", apellidos="Lopez")
    assert a.email is None
