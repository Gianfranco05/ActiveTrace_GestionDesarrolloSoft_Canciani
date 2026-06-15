"""TDD: CalificacionService tests — import preview, confirm, reporte-finalizacion."""

import io
import uuid
from datetime import datetime, timezone

import pytest
from openpyxl import Workbook

from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import UmbralMateria
from app.services.calificacion_service import CalificacionService


def _make_xlsx(headers: list, rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def _create_prereqs(
    db_session, tenant,
    materia_codigo="CS-MAT", materia_nombre="CS Test",
    cohorte_nombre="CS-2026",
):
    carrera = Carrera(codigo="CS-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    materia = Materia(codigo=materia_codigo, nombre=materia_nombre, tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre=cohorte_nombre, anio=2026,
        vig_desde=datetime.now(timezone.utc).date(), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    auth_user = AuthUser(tenant_id=tenant.id, email="cs@test.com", password_hash="hash")
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(id=auth_user.id, tenant_id=tenant.id, nombre="CS", apellidos="Test")
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    return {"materia": materia, "cohorte": cohorte, "usuario": usuario}


async def _create_padron(db_session, tenant, materia, cohorte, entries_data: list[dict]):
    """Create version_padron + entries, return version."""
    vp = VersionPadron(tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, activa=True)
    db_session.add(vp)
    await db_session.flush()
    entries = []
    for ed in entries_data:
        ep = EntradaPadron(tenant_id=tenant.id, version_id=vp.id, **ed)
        db_session.add(ep)
        entries.append(ep)
    await db_session.commit()
    for e in entries:
        await db_session.refresh(e)
    await db_session.refresh(vp)
    return vp, entries


# ===== Group 8: Import Preview + Confirm =====


@pytest.mark.asyncio
async def test_preview_returns_detected_activities(db_session, tenant):
    """RED 8.1: Preview returns detected activities and preview rows."""
    prereqs = await _create_prereqs(db_session, tenant)
    headers = ["nombre", "apellidos", "email", "TP1 (Real)", "Participacion"]
    rows = [["Ana", "Lopez", "ana@test.com", 75, "Satisfactorio"] for _ in range(200)]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.preview(content, "test.xlsx")

    assert result["filename"] == "test.xlsx"
    assert result["total_rows"] == 200
    assert len(result["preview_rows"]) == 20
    assert len(result["actividades_detectadas"]) == 2

    activities = {a["nombre"]: a["tipo"] for a in result["actividades_detectadas"]}
    assert activities["TP1"] == "Numerica"
    assert activities["Participacion"] == "Textual"


@pytest.mark.asyncio
async def test_preview_is_idempotent(db_session, tenant):
    """TRIANGULATE: Preview has no side effects."""
    prereqs = await _create_prereqs(db_session, tenant)
    headers = ["nombre", "apellidos", "TP1 (Real)"]
    rows = [["Ana", "Lopez", 75]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    await svc.preview(content, "test.xlsx")
    await svc.preview(content, "test.xlsx")

    from app.models.calificacion import Calificacion
    from sqlalchemy import select, func
    result = await db_session.execute(select(func.count()).select_from(Calificacion))
    assert result.scalar_one() == 0


@pytest.mark.asyncio
async def test_confirm_import_creates_calificaciones(db_session, tenant):
    """TRIANGULATE 8.4: Confirm import creates calificaciones."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    headers = ["nombre", "apellidos", "email", "TP1 (Real)", "Participacion"]
    rows = [["Ana", "Lopez", "ana@test.com", 75, "Satisfactorio"]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.confirm_import(content, "test.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert result["calificaciones_creadas"] == 2
    assert result["materia_id"] == prereqs["materia"].id
    assert result["cohorte_id"] == prereqs["cohorte"].id


@pytest.mark.asyncio
async def test_confirm_import_derives_aprobado(db_session, tenant):
    """TRIANGULATE 8.4: Aprobado derived correctly."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    # Set umbral to 60
    um = UmbralMateria(tenant_id=tenant.id, materia_id=prereqs["materia"].id, umbral_pct=60)
    um.valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]
    db_session.add(um)
    await db_session.commit()

    headers = ["nombre", "apellidos", "email", "TP1 (Real)", "TP2 (Real)", "Participacion"]
    rows = [["Ana", "Lopez", "ana@test.com", 75, 45, "No satisfactorio"]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.confirm_import(content, "test.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)
    assert result["calificaciones_creadas"] == 3

    from app.models.calificacion import Calificacion
    from sqlalchemy import select
    all_califs = (await db_session.execute(select(Calificacion))).scalars().all()

    calif_map = {c.actividad: c for c in all_califs}
    assert calif_map["TP1 (Real)"].aprobado is True
    assert calif_map["TP2 (Real)"].aprobado is False
    assert calif_map["Participacion"].aprobado is False


@pytest.mark.asyncio
async def test_confirm_import_no_umbral_uses_default(db_session, tenant):
    """TRIANGULATE 8.4: No umbral uses default 60%."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    headers = ["nombre", "apellidos", "email", "TP1 (Real)"]
    rows = [["Ana", "Lopez", "ana@test.com", 60]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.confirm_import(content, "test.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)
    assert result["calificaciones_creadas"] == 1


@pytest.mark.asyncio
async def test_confirm_import_non_existent_materia_raises(db_session, tenant):
    """TRIANGULATE 8.4: Non-existent materia raises."""
    headers = ["nombre", "apellidos", "TP1 (Real)"]
    rows = [["Ana", "Lopez", 75]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, uuid.uuid4())
    with pytest.raises(Exception) as exc:
        await svc.confirm_import(content, "test.xlsx", uuid.uuid4(), uuid.uuid4())
    assert "404" in str(exc.type) or "404" in str(exc.value)


@pytest.mark.asyncio
async def test_confirm_import_with_actividad_mapping(db_session, tenant):
    """TRIANGULATE 8.4: actividad_mapping renames columns."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    headers = ["nombre", "apellidos", "email", "TP1 (Real)"]
    rows = [["Ana", "Lopez", "ana@test.com", 75]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.confirm_import(
        content, "test.xlsx",
        prereqs["materia"].id, prereqs["cohorte"].id,
        actividad_mapping={"TP1 (Real)": "Trabajo Practico 1"},
    )
    assert result["calificaciones_creadas"] == 1

    from app.models.calificacion import Calificacion
    from sqlalchemy import select
    calif = (await db_session.execute(select(Calificacion))).scalar_one()
    assert calif.actividad == "Trabajo Practico 1"


# ===== Group 9: Reporte Finalización =====


@pytest.mark.asyncio
async def test_reporte_finalizacion_detects_pending(db_session, tenant):
    """RED 9.1: Reporte detects textual activities pending review."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    # Completion report: mixed textual and numeric
    headers = ["nombre", "apellidos", "TP Escrito", "Participacion", "TP1 (Real)"]
    rows = [["Ana", "Lopez", "Entregado", "Completado", 80]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "reporte.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert result["total_actividades_revisadas"] == 2  # Only textual
    assert len(result["posibles_sin_corregir"]) == 2  # Both textual activities pending


@pytest.mark.asyncio
async def test_reporte_skips_numeric_activities(db_session, tenant):
    """TRIANGULATE 9.4: Numeric activities excluded from review."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    headers = ["nombre", "apellidos", "TP1 (Real)"]
    rows = [["Ana", "Lopez", 80]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "r.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert result["total_actividades_revisadas"] == 0  # None textual = nothing reviewed
    assert len(result["posibles_sin_corregir"]) == 0


@pytest.mark.asyncio
async def test_reporte_excludes_graded_activities(db_session, tenant):
    """TRIANGULATE 9.4: Activities with existing grades excluded."""
    prereqs = await _create_prereqs(db_session, tenant)
    vp, entries = await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    # Create a calificacion for "TP Escrito"
    from app.models.calificacion import Calificacion
    calif = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=entries[0].id,
        actividad="TP Escrito",
        tipo="Textual",
        nota_textual="Satisfactorio",
        aprobado=True,
        origen="Importado",
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(calif)
    await db_session.commit()

    headers = ["nombre", "apellidos", "TP Escrito"]
    rows = [["Ana", "Lopez", "Entregado"]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "r.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert result["total_actividades_revisadas"] == 1
    assert len(result["posibles_sin_corregir"]) == 0


@pytest.mark.asyncio
async def test_reporte_excludes_non_submitted(db_session, tenant):
    """TRIANGULATE 9.4: Non-submitted activities excluded."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    headers = ["nombre", "apellidos", "TP Escrito"]
    rows = [["Ana", "Lopez", "No entregado"]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "r.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert len(result["posibles_sin_corregir"]) == 0


@pytest.mark.asyncio
async def test_reporte_grouped_by_actividad(db_session, tenant):
    """TRIANGULATE 9.4: Report grouped by actividad."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
        {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
    ])

    headers = ["nombre", "apellidos", "TP Escrito", "Participacion"]
    rows = [
        ["Ana", "Lopez", "Entregado", "Entregado"],
        ["Juan", "Perez", "Entregado", "No entregado"],
    ]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "r.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert len(result["posibles_sin_corregir"]) == 2  # Both activities have pending
    for item in result["posibles_sin_corregir"]:
        if item["actividad"] == "Participacion":
            assert len(item["alumnos"]) == 1  # Only Ana submitted
        elif item["actividad"] == "TP Escrito":
            assert len(item["alumnos"]) == 2  # Both submitted


@pytest.mark.asyncio
async def test_reporte_empty_when_all_graded(db_session, tenant):
    """TRIANGULATE 9.4: Empty cuando todo corregido."""
    prereqs = await _create_prereqs(db_session, tenant)
    vp, entries = await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    from app.models.calificacion import Calificacion
    calif = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=entries[0].id,
        actividad="TP Escrito", tipo="Textual",
        nota_textual="Satisfactorio", aprobado=True,
        origen="Importado", cargado_por=prereqs["usuario"].id,
    )
    db_session.add(calif)
    await db_session.commit()

    headers = ["nombre", "apellidos", "TP Escrito"]
    rows = [["Ana", "Lopez", "Entregado"]]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "r.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert len(result["posibles_sin_corregir"]) == 0


@pytest.mark.asyncio
async def test_reporte_handles_unmatched_students(db_session, tenant):
    """TRIANGULATE 9.4: Unmatched students handled gracefully."""
    prereqs = await _create_prereqs(db_session, tenant)
    await _create_padron(db_session, tenant, prereqs["materia"], prereqs["cohorte"], [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    headers = ["nombre", "apellidos", "TP Escrito"]
    rows = [
        ["Ana", "Lopez", "Entregado"],
        ["NoExiste", "Nadie", "Entregado"],
    ]
    content = _make_xlsx(headers, rows)

    svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)
    result = await svc.reporte_finalizacion(content, "r.xlsx", prereqs["materia"].id, prereqs["cohorte"].id)

    assert len(result["posibles_sin_corregir"]) == 1
    assert len(result["posibles_sin_corregir"][0]["alumnos"]) == 1
    assert result["posibles_sin_corregir"][0]["alumnos"][0]["nombre"] == "Ana"
