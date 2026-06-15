"""TDD 16.1: Calificaciones integration — full E2E flow."""

from datetime import date
import io

import pytest
from openpyxl import Workbook

from app.models.calificacion import Calificacion
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.padron import VersionPadron, EntradaPadron
from app.services.calificacion_service import CalificacionService
from app.services.umbral_service import UmbralService


def _make_xlsx_bytes(headers: list[str], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def _create_prereqs(db_session, tenant) -> dict:
    carrera = Carrera(codigo="INT-CAR", nombre="Integration Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    materia = Materia(codigo="INT-MAT", nombre="Integration Materia", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="INT-2026", anio=2026,
        vig_desde=date(2026, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    auth_user = AuthUser(tenant_id=tenant.id, email="int@test.com", password_hash="hash")
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(id=auth_user.id, tenant_id=tenant.id, nombre="Int", apellidos="Test")
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    vp = VersionPadron(
        tenant_id=tenant.id, materia_id=materia.id,
        cohorte_id=cohorte.id, activa=True, cargado_por=usuario.id,
    )
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)

    entries_data = [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
        {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
        {"nombre": "Maria", "apellidos": "Garcia", "email": "maria@test.com"},
    ]
    entries = []
    for ed in entries_data:
        ep = EntradaPadron(tenant_id=tenant.id, version_id=vp.id, **ed)
        db_session.add(ep)
        entries.append(ep)
    await db_session.commit()
    for e in entries:
        await db_session.refresh(e)

    return {
        "materia": materia, "cohorte": cohorte, "usuario": usuario,
        "entries": entries,
    }


@pytest.mark.asyncio
async def test_calificaciones_full_flow(db_session, tenant):
    """16.1: Full E2E: umbral → preview → confirm → verify → reporte."""
    prereqs = await _create_prereqs(db_session, tenant)
    materia = prereqs["materia"]
    cohorte = prereqs["cohorte"]
    usuario = prereqs["usuario"]
    entries = prereqs["entries"]

    # === Step 1: Set umbral to 60% ===
    umbral_svc = UmbralService(db_session, tenant.id)
    umbral_result = await umbral_svc.set_umbral(materia.id, 60)
    assert umbral_result["umbral_pct"] == 60

    # === Step 2: Preview import ===
    headers = ["nombre", "apellidos", "email", "TP1 (Real)", "TP2 (Real)", "Participacion"]
    rows = [
        ["Ana", "Lopez", "ana@test.com", 75, 45, "Satisfactorio"],
        ["Juan", "Perez", "juan@test.com", 80, 55, "No satisfactorio"],
        ["Maria", "Garcia", "maria@test.com", 30, 90, "Supera lo esperado"],
    ]
    content = _make_xlsx_bytes(headers, rows)

    calif_svc = CalificacionService(db_session, tenant.id, usuario.id)
    preview = await calif_svc.preview(content, "test.xlsx")
    assert preview["total_rows"] == 3
    assert len(preview["actividades_detectadas"]) == 3

    activities = {a["nombre"]: a["tipo"] for a in preview["actividades_detectadas"]}
    assert activities["TP1"] == "Numerica"
    assert activities["TP2"] == "Numerica"
    assert activities["Participacion"] == "Textual"

    # === Step 3: Confirm import ===
    confirm_result = await calif_svc.confirm_import(
        content, "test.xlsx", materia.id, cohorte.id,
    )
    assert confirm_result["calificaciones_creadas"] == 9  # 3 students × 3 activities

    # === Step 4: Verify calificaciones with derived aprobado ===
    from sqlalchemy import select
    all_califs = (await db_session.execute(
        select(Calificacion).where(Calificacion.materia_id == materia.id),
    )).scalars().all()

    assert len(all_califs) == 9

    # Ana: TP1=75(aprobado), TP2=45(no), Participacion=Satisfactorio(aprobado)
    ana_califs = {c.actividad: c for c in all_califs
                  if c.entrada_padron_id == entries[0].id}
    assert ana_califs["TP1 (Real)"].aprobado is True   # 75 >= 60
    assert ana_califs["TP2 (Real)"].aprobado is False   # 45 < 60
    assert ana_califs["Participacion"].aprobado is True  # Satisfactorio

    # Juan: TP1=80(aprobado), TP2=55(no), Participacion=No satisfactorio(no)
    juan_califs = {c.actividad: c for c in all_califs
                   if c.entrada_padron_id == entries[1].id}
    assert juan_califs["TP1 (Real)"].aprobado is True
    assert juan_califs["TP2 (Real)"].aprobado is False
    assert juan_califs["Participacion"].aprobado is False

    # Maria: TP1=30(no), TP2=90(aprobado), Participacion=Supera lo esperado(aprobado)
    maria_califs = {c.actividad: c for c in all_califs
                    if c.entrada_padron_id == entries[2].id}
    assert maria_califs["TP1 (Real)"].aprobado is False
    assert maria_califs["TP2 (Real)"].aprobado is True
    assert maria_califs["Participacion"].aprobado is True

    # Check all have origen=Importado
    for c in all_califs:
        assert c.origen == "Importado"
        assert c.cargado_por == usuario.id
        assert c.importado_at is not None

    # === Step 5: Reporte de finalización (detect pending textual) ===
    report_headers = ["nombre", "apellidos", "Participacion", "TP Escrito"]
    report_rows = [
        ["Ana", "Lopez", "Entregado", "Entregado"],       # Participacion already graded
        ["Juan", "Perez", "Entregado", "Entregado"],
        ["Maria", "Garcia", "No entregado", "Entregado"],  # Participacion not submitted
    ]
    report_content = _make_xlsx_bytes(report_headers, report_rows)

    reporte = await calif_svc.reporte_finalizacion(
        report_content, "reporte.xlsx", materia.id, cohorte.id,
    )

    assert reporte["total_actividades_revisadas"] == 2  # Participacion + TP Escrito (both textual)

    # Participacion — Ana and Juan already have grades, Maria didn't submit → 0 pending
    # TP Escrito — all 3 submitted but none graded → 3 pending
    pending_map = {r["actividad"]: r["alumnos"] for r in reporte["posibles_sin_corregir"]}

    assert "Participacion" not in pending_map  # Already has grades
    assert "TP Escrito" in pending_map
    assert len(pending_map["TP Escrito"]) == 3  # All 3 submitted

    # === Step 6: Get umbral ===
    get_umbral = await umbral_svc.get_umbral(materia.id)
    assert get_umbral["umbral_pct"] == 60

    # === Step 7: Update umbral ===
    update_umbral = await umbral_svc.set_umbral(materia.id, 75)
    assert update_umbral["umbral_pct"] == 75

    # Verify existing calificaciones unchanged (aprobado NOT recalculated)
    ana_tp1 = (await db_session.execute(
        select(Calificacion).where(
            Calificacion.id == ana_califs["TP1 (Real)"].id,
        ),
    )).scalar_one()
    assert ana_tp1.aprobado is True  # Still True, NOT recalculated


@pytest.mark.asyncio
async def test_calificaciones_preview_idempotent_no_side_effects(db_session, tenant):
    """16.1: Preview does not create any calificaciones."""
    prereqs = await _create_prereqs(db_session, tenant)

    headers = ["nombre", "apellidos", "email", "TP1 (Real)"]
    rows = [["Ana", "Lopez", "ana@test.com", 75]]
    content = _make_xlsx_bytes(headers, rows)

    from sqlalchemy import select, func
    calif_svc = CalificacionService(db_session, tenant.id, prereqs["usuario"].id)

    await calif_svc.preview(content, "test.xlsx")
    await calif_svc.preview(content, "test.xlsx")
    await calif_svc.preview(content, "test.xlsx")

    count = (await db_session.execute(
        select(func.count()).select_from(Calificacion),
    )).scalar_one()
    assert count == 0


@pytest.mark.asyncio
async def test_umbral_get_set_lifecycle(db_session, tenant):
    """16.1: Umbral get (defaults) → set → get (updated)."""
    prereqs = await _create_prereqs(db_session, tenant)

    svc = UmbralService(db_session, tenant.id)

    # Defaults
    default = await svc.get_umbral(prereqs["materia"].id)
    assert default["umbral_pct"] == 60
    assert default["valores_aprobatorios"] == ["Satisfactorio", "Supera lo esperado"]

    # Set
    updated = await svc.set_umbral(prereqs["materia"].id, 70)
    assert updated["umbral_pct"] == 70

    # Get updated
    fetched = await svc.get_umbral(prereqs["materia"].id)
    assert fetched["umbral_pct"] == 70
