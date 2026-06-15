"""TDD: AtrasadosService tests — RED → GREEN → TRIANGULATE."""

from datetime import datetime, timezone

import pytest

from app.models.calificacion import Calificacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.services.analisis.atrasados_service import AtrasadosService


async def _seed_carrera(db_session, tenant, codigo="ATR-CAR"):
    carrera = Carrera(codigo=codigo, nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)
    return carrera


async def _seed_materia_cohorte(db_session, tenant, codigo="ATR-MAT", coh_nombre="ATR-2026"):
    carrera = await _seed_carrera(db_session, tenant, codigo=f"{codigo}-CAR")
    materia = Materia(codigo=codigo, nombre=f"Analisis {codigo}", tenant_id=tenant.id)
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
    au = AuthUser(tenant_id=tenant.id, email="atr@test.com", password_hash="hash")
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


@pytest.mark.asyncio
async def test_detect_atrasados_por_faltantes(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    # Seed 5 distinct activities for this materia×cohorte (by adding to another student)
    vp2, entries2 = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Otro", "apellidos": "Alumno", "email": "otro@test.com"},
    ])
    for i in range(5):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries2[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=80)

    # Student Ana only has 3 of the 5 activities
    for i in range(3):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=80)

    svc = AtrasadosService(db_session, tenant.id)
    result = await svc.get_atrasados(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].nombre == "Ana"
    assert result.items[0].motivo == "actividades_faltantes"
    assert result.sin_datos is False


@pytest.mark.asyncio
async def test_detect_atrasados_por_nota_baja(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    for i in range(2):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP3", "Numerica", False, usuario.id, nota_numerica=40)

    svc = AtrasadosService(db_session, tenant.id)
    result = await svc.get_atrasados(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].motivo == "nota_baja"
    assert "TP3" in result.items[0].actividades_reprobadas


@pytest.mark.asyncio
async def test_detect_atrasados_ambos(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    # Seed 3 distinct activities via another student
    vp2, entries2 = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Otro", "apellidos": "Alumno"},
    ])
    for i in range(3):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries2[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=80)

    # Ana has only 2 of 3: 1 approved, 1 reprobated → missing 1, reprobated 1
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP2", "Numerica", False, usuario.id, nota_numerica=30)

    svc = AtrasadosService(db_session, tenant.id)
    result = await svc.get_atrasados(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].motivo == "ambos"
    assert len(result.items[0].actividades_faltantes) >= 1
    assert len(result.items[0].actividades_reprobadas) >= 1


@pytest.mark.asyncio
async def test_alumno_al_dia_no_incluido(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
    ])

    for i in range(3):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=85)

    svc = AtrasadosService(db_session, tenant.id)
    result = await svc.get_atrasados(materia.id, cohorte.id)

    assert len(result.items) == 0
    assert result.total == 0


@pytest.mark.asyncio
async def test_sin_calificaciones_todos_atrasados(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com"},
        {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
    ])

    svc = AtrasadosService(db_session, tenant.id)
    result = await svc.get_atrasados(materia.id, cohorte.id)

    assert len(result.items) == 2
    assert result.sin_datos is True
    for item in result.items:
        assert item.motivo == "actividades_faltantes"


@pytest.mark.asyncio
async def test_atrasados_filter_by_materia_cohorte(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant, codigo="FILTRO-MAT1", coh_nombre="F1")
    materia2, cohorte2 = await _seed_materia_cohorte(db_session, tenant, codigo="FILTRO-MAT2", coh_nombre="F2")
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    vp2, entries2 = await _seed_padron(db_session, tenant, materia2, cohorte2, [
        {"nombre": "Juan", "apellidos": "Perez"},
    ])

    svc = AtrasadosService(db_session, tenant.id)
    result1 = await svc.get_atrasados(materia.id, cohorte.id)
    assert len(result1.items) == 1
    assert result1.items[0].nombre == "Ana"

    result2 = await svc.get_atrasados(materia2.id, cohorte2.id)
    assert len(result2.items) == 1
    assert result2.items[0].nombre == "Juan"
