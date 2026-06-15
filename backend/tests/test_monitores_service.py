"""TDD: MonitoresService tests — general, seguimiento, coordinacion."""

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
from app.services.analisis.monitores_service import MonitoresService


async def _seed_materia_cohorte(db_session, tenant, codigo="MON-MAT", coh_nombre="MON-2026"):
    carrera = Carrera(codigo=f"{codigo}-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)
    materia = Materia(codigo=codigo, nombre=f"Monitor {codigo}", tenant_id=tenant.id)
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
    au = AuthUser(tenant_id=tenant.id, email="mon@test.com", password_hash="hash")
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


# ===== Group 8: Monitor General =====


@pytest.mark.asyncio
async def test_monitor_general_cross_materia(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant, codigo="MON-G1", coh_nombre="G1")
    materia2, cohorte2 = await _seed_materia_cohorte(db_session, tenant, codigo="MON-G2", coh_nombre="G2")
    usuario = await _seed_usuario(db_session, tenant)

    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    vp2, entries2 = await _seed_padron(db_session, tenant, materia2, cohorte2, [
        {"nombre": "Juan", "apellidos": "Perez"},
    ])
    await _seed_calificacion(db_session, tenant, materia2, cohorte2, entries2[0],
                             "TP1", "Numerica", False, usuario.id, nota_numerica=30)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_monitor_general()

    assert len(result) == 2
    mat1 = next(r for r in result if r.materia_id == materia.id)
    mat2 = next(r for r in result if r.materia_id == materia2.id)
    assert mat1.total_alumnos == 1
    assert mat1.aprobados == 1
    assert mat1.atrasados == 0
    assert mat2.total_alumnos == 1
    assert mat2.aprobados == 0
    assert mat2.atrasados == 1


@pytest.mark.asyncio
async def test_monitor_general_row_format(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_monitor_general()

    assert len(result) >= 1
    row = result[0]
    assert row.materia_id is not None
    assert row.materia_nombre != ""
    assert row.pct_aprobacion >= Decimal("0")


# ===== Group 9: Monitor Seguimiento =====


@pytest.mark.asyncio
async def test_monitor_seguimiento_scoped_to_user(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant, codigo="MON-S1", coh_nombre="S1")
    materia2, cohorte2 = await _seed_materia_cohorte(db_session, tenant, codigo="MON-S2", coh_nombre="S2")
    usuario = await _seed_usuario(db_session, tenant)

    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    vp2, entries2 = await _seed_padron(db_session, tenant, materia2, cohorte2, [
        {"nombre": "Juan", "apellidos": "Perez"},
    ])
    await _seed_calificacion(db_session, tenant, materia2, cohorte2, entries2[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=90)

    # Seguimiento with materia_id filter
    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_seguimiento(materia.id)

    assert len(result) == 1
    assert result[0].nombre == "Ana"
    assert result[0].actividades_aprobadas == 1


@pytest.mark.asyncio
async def test_monitor_seguimiento_filtered_by_materia(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    materia2, cohorte2 = await _seed_materia_cohorte(db_session, tenant, codigo="MON-SF", coh_nombre="SF")
    usuario = await _seed_usuario(db_session, tenant)

    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
        {"nombre": "Luis", "apellidos": "Gomez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_seguimiento(materia.id)
    # Only students from materia
    assert len(result) == 2  # Both entries from materia
    ana = next(r for r in result if r.nombre == "Ana")
    luis = next(r for r in result if r.nombre == "Luis")
    assert ana.actividades_aprobadas == 1
    assert luis.actividades_aprobadas == 0
    assert luis.estado == "Sin datos"  # No califs


@pytest.mark.asyncio
async def test_monitor_seguimiento_student_status_al_dia(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    # 2 approved of 2 activities → 100% → Al día
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP2", "Numerica", True, usuario.id, nota_numerica=75)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_seguimiento(materia.id)

    assert len(result) == 1
    assert result[0].estado == "Al día"


@pytest.mark.asyncio
async def test_monitor_seguimiento_student_status_atrasado(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    # 1 approved of 2 activities → 50% → Atrasado
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP2", "Numerica", False, usuario.id, nota_numerica=30)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_seguimiento(materia.id)

    assert len(result) == 1
    assert result[0].estado == "Atrasado"


# ===== Group 10: Monitor Coordinación =====


@pytest.mark.asyncio
async def test_monitor_coordinacion_date_range_filter(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    desde = datetime(2020, 1, 1, tzinfo=timezone.utc)
    hasta = datetime(2020, 12, 31, tzinfo=timezone.utc)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_coordinacion(desde=desde, hasta=hasta)

    # Our calificacion has importado_at = now (way past 2020), so metrics should be 0
    assert len(result) == 1
    assert result[0].aprobados == 0
    assert result[0].atrasados == 0
    assert result[0].total_alumnos == 1
    assert result[0].period_desde == desde
    assert result[0].period_hasta == hasta


@pytest.mark.asyncio
async def test_monitor_coordinacion_sin_filtros(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_coordinacion()

    assert len(result) == 1
    assert result[0].materia_id == materia.id
    assert result[0].aprobados == 1


@pytest.mark.asyncio
async def test_monitor_coordinacion_filtered_by_materia(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant, codigo="MON-C1", coh_nombre="C1")
    materia2, cohorte2 = await _seed_materia_cohorte(db_session, tenant, codigo="MON-C2", coh_nombre="C2")
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    vp2, entries2 = await _seed_padron(db_session, tenant, materia2, cohorte2, [
        {"nombre": "Juan", "apellidos": "Perez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia2, cohorte2, entries2[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=85)

    svc = MonitoresService(db_session, tenant.id)
    result = await svc.get_coordinacion(materia_id=materia.id)

    assert len(result) == 1
    assert result[0].materia_id == materia.id
