"""TDD: RankingService + NotasFinalesService tests."""

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
from app.services.analisis.ranking_service import NotasFinalesService, RankingService


async def _seed_materia_cohorte(db_session, tenant, codigo="RNK-MAT", coh_nombre="RNK-2026"):
    carrera = Carrera(codigo=f"{codigo}-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)
    materia = Materia(codigo=codigo, nombre=f"Ranking {codigo}", tenant_id=tenant.id)
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
    au = AuthUser(tenant_id=tenant.id, email="rnk@test.com", password_hash="hash")
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


# ===== Group 4: Ranking =====


@pytest.mark.asyncio
async def test_ranking_returns_sorted_by_approved(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
        {"nombre": "Juan", "apellidos": "Perez"},
        {"nombre": "Luis", "apellidos": "Gomez"},
        {"nombre": "Sofia", "apellidos": "Diaz"},
    ])
    # A: 4 approved, J: 2 approved, L: 1 approved, S: 0 approved (excluded)
    for i in range(4):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=80)
    for i in range(2):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[1],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=75)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[2],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=70)
    # Sofia has 0 approved activities (has califs but all reprobated)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[3],
                             "TP1", "Numerica", False, usuario.id, nota_numerica=30)

    svc = RankingService(db_session, tenant.id)
    result = await svc.get_ranking(materia.id, cohorte.id)

    assert len(result.items) == 3  # Only A, J, L (S excluded)
    assert result.items[0].nombre == "Ana"
    assert result.items[0].aprobadas == 4
    assert result.items[1].nombre == "Juan"
    assert result.items[1].aprobadas == 2
    assert result.items[2].nombre == "Luis"
    assert result.items[2].aprobadas == 1
    assert result.total_aprobados == 3


@pytest.mark.asyncio
async def test_ranking_excludes_zero_approved(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
        {"nombre": "Juan", "apellidos": "Perez"},
    ])
    # Both are in padron but Ana has 0 approved activities
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[1],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    svc = RankingService(db_session, tenant.id)
    result = await svc.get_ranking(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].nombre == "Juan"


@pytest.mark.asyncio
async def test_ranking_ties_alphabetical(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Carlos", "apellidos": "Baca"},
        {"nombre": "Ana", "apellidos": "Aguirre"},
        {"nombre": "Luis", "apellidos": "Castro"},
    ])
    # All have 1 approved activity → tie → alphabetical by apellidos
    for e in entries:
        await _seed_calificacion(db_session, tenant, materia, cohorte, e,
                                 "TP1", "Numerica", True, usuario.id, nota_numerica=80)

    svc = RankingService(db_session, tenant.id)
    result = await svc.get_ranking(materia.id, cohorte.id)

    assert len(result.items) == 3
    assert result.items[0].apellidos == "Aguirre"
    assert result.items[1].apellidos == "Baca"
    assert result.items[2].apellidos == "Castro"


@pytest.mark.asyncio
async def test_ranking_empty_when_no_approved(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", False, usuario.id, nota_numerica=30)

    svc = RankingService(db_session, tenant.id)
    result = await svc.get_ranking(materia.id, cohorte.id)

    assert len(result.items) == 0
    assert result.total_aprobados == 0


# ===== Group 5: Notas Finales =====


@pytest.mark.asyncio
async def test_notas_finales_average(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Numerica", True, usuario.id, nota_numerica=80)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP2", "Numerica", True, usuario.id, nota_numerica=90)
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP3", "Numerica", True, usuario.id, nota_numerica=70)

    svc = NotasFinalesService(db_session, tenant.id)
    result = await svc.get_notas(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].nota_promedio == Decimal("80.00")
    assert result.items[0].actividades_aprobadas == 3


@pytest.mark.asyncio
async def test_notas_finales_textual_only_is_null(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                             "TP1", "Textual", True, usuario.id, nota_textual="Satisfactorio")

    svc = NotasFinalesService(db_session, tenant.id)
    result = await svc.get_notas(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].nota_promedio is None


@pytest.mark.asyncio
async def test_notas_finales_sin_datos(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])

    svc = NotasFinalesService(db_session, tenant.id)
    result = await svc.get_notas(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].estado == "Sin datos"
    assert result.items[0].nota_promedio is None


@pytest.mark.asyncio
async def test_notas_finales_state_derivation_regular(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    # 3 of 5 approved = 60% → Regular
    for i in range(3):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=75)
    for i in range(3, 5):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", False, usuario.id, nota_numerica=40)

    svc = NotasFinalesService(db_session, tenant.id)
    result = await svc.get_notas(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].estado == "Regular"


@pytest.mark.asyncio
async def test_notas_finales_state_derivation_libre(db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    vp, entries = await _seed_padron(db_session, tenant, materia, cohorte, [
        {"nombre": "Ana", "apellidos": "Lopez"},
    ])
    # 2 of 5 approved = 40% → Libre
    for i in range(2):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", True, usuario.id, nota_numerica=75)
    for i in range(2, 5):
        await _seed_calificacion(db_session, tenant, materia, cohorte, entries[0],
                                 f"TP{i+1}", "Numerica", False, usuario.id, nota_numerica=40)

    svc = NotasFinalesService(db_session, tenant.id)
    result = await svc.get_notas(materia.id, cohorte.id)

    assert len(result.items) == 1
    assert result.items[0].estado == "Libre"
