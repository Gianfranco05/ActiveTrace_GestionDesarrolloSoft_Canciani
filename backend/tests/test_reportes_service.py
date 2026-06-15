"""TDD: ReportesService + ExportService tests."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.calificacion import Calificacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.services.analisis.reportes_service import ExportService, ReportesService


async def _seed_materia_cohorte(db_session, tenant, codigo="RPT-MAT", coh_nombre="RPT-2026"):
    carrera = Carrera(codigo=f"{codigo}-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)
    materia = Materia(codigo=codigo, nombre=f"Reporte {codigo}", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)
    cohorte = Cohorte(
        carrera_id=carrera.id, nombre=coh_nombre, anio=2026,
        vig_desde=datetime.now(timezone.utc).date(), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)
    return materia, cohorte


async def _seed_usuario(db_session, tenant):
    au = AuthUser(tenant_id=tenant.id, email="rpt@test.com", password_hash="hash")
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Test", apellidos="User")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _seed_padron(db_session, tenant, materia, cohorte, entries_data):
    vp = VersionPadron(
        tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, activa=True,
    )
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


async def _seed_calificacion(db_session, tenant, materia, cohorte, entrada, actividad, tipo, aprobado, usuario_id, nota_numerica=None, nota_textual=None):
    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        entrada_padron_id=entrada.id,
        actividad=actividad,
        tipo=tipo,
        nota_numerica=nota_numerica,
        nota_textual=nota_textual,
        aprobado=aprobado,
        origen="Importado",
        cargado_por=usuario_id,
        importado_at=datetime.now(timezone.utc),
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


# ===== Group 6: Reportes =====


@pytest.mark.asyncio
async def test_reporte_materia_aggregates(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
        {"nombre": "Juan", "apellidos": "Perez"},
        {"nombre": "Luis", "apellidos": "Gomez"},
    ])
    # Ana: 2 approved activities
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP2", "Numerica", True, usuario.id, nota_numerica=75)
    # Juan: 1 approved, 1 reprobated
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[1],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=70)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[1],
                             "TP2", "Numerica", False, usuario.id, nota_numerica=30)
    # Luis: no calificaciones → atrasado

    svc = ReportesService(db_session, tenant.id)
    result = await svc.get_reporte(materia.id)

    assert result.total_alumnos == 3
    assert result.alumnos_con_nota == 2  # Ana + Juan
    assert result.alumnos_aprobados == 2  # Ana + Juan (both have >=1 approved)
    assert result.alumnos_atrasados == 2  # Juan (1 reprobated) + Luis (no grades)
    assert result.actividades_count == 2
    assert result.sin_datos is False
    assert result.pct_aprobados > Decimal("0")
    assert result.pct_atrasados > Decimal("0")


@pytest.mark.asyncio
async def test_reporte_materia_sin_datos(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])

    svc = ReportesService(db_session, tenant.id)
    result = await svc.get_reporte(materia.id)

    assert result.total_alumnos == 1
    assert result.alumnos_con_nota == 0
    assert result.alumnos_atrasados == 1
    assert result.sin_datos is True
    assert result.ultima_importacion is None


@pytest.mark.asyncio
async def test_reporte_materia_response_format(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    svc = ReportesService(db_session, tenant.id)
    result = await svc.get_reporte(materia.id)

    assert result.materia_id == materia.id
    assert result.materia_nombre == materia.nombre
    assert result.cohorte_id is not None


# ===== Group 7: Export TPs =====


@pytest.mark.asyncio
async def test_export_tps_sin_corregir_csv(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com", "comision": "A"},
        {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com", "comision": "A"},
    ])
    # TP Escrito: textual, no grade → pending
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP Escrito", "Textual", False, usuario.id,
                             nota_textual=None)
    # Participacion: textual, no grade → pending
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[1],
                             "Participacion", "Textual", False, usuario.id,
                             nota_textual=None)

    svc = ExportService(db_session, tenant.id)
    result = await svc.export_tps_sin_corregir(materia.id, cohorte.id)

    assert len(result) == 2
    assert all(r.actividad in ("TP Escrito", "Participacion") for r in result)


@pytest.mark.asyncio
async def test_export_excludes_numeric_without_grade(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    # Numeric, no grade → NOT included (RN-08)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", False, usuario.id, nota_numerica=None)
    # Textual, no grade → included
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP Escrito", "Textual", False, usuario.id, nota_textual=None)

    svc = ExportService(db_session, tenant.id)
    result = await svc.export_tps_sin_corregir(materia.id, cohorte.id)

    assert len(result) == 1
    assert result[0].actividad == "TP Escrito"


@pytest.mark.asyncio
async def test_export_excludes_graded_textual(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    # Textual, graded → NOT included
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP Escrito", "Textual", True, usuario.id,
                             nota_textual="Satisfactorio")

    svc = ExportService(db_session, tenant.id)
    result = await svc.export_tps_sin_corregir(materia.id, cohorte.id)

    assert len(result) == 0


@pytest.mark.asyncio
async def test_export_empty_csv(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])

    svc = ExportService(db_session, tenant.id)
    result = await svc.export_tps_sin_corregir(materia.id, cohorte.id)

    assert len(result) == 0
