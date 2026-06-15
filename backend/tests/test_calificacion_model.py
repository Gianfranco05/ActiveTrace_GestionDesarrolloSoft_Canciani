"""TDD: Calificacion + UmbralMateria model tests."""

import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa

from app.models.calificacion import Calificacion, UmbralMateria
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.padron import VersionPadron, EntradaPadron


# ===== Group 1: Calificacion Model =====


async def _create_prereqs(db_session, tenant) -> dict:
    carrera = Carrera(codigo="CAL-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    materia = Materia(codigo="CAL-MAT", nombre="Test Materia", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="CAL-2026", anio=2026,
        vig_desde=datetime.now(timezone.utc).date(), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    auth_user = AuthUser(tenant_id=tenant.id, email="cal@test.com", password_hash="hash")
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(id=auth_user.id, tenant_id=tenant.id, nombre="Cal", apellidos="Test")
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    vp = VersionPadron(tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id)
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)

    ep = EntradaPadron(tenant_id=tenant.id, version_id=vp.id, nombre="Ana", apellidos="Lopez", email="ana@test.com")
    db_session.add(ep)
    await db_session.commit()
    await db_session.refresh(ep)

    return {
        "materia": materia, "cohorte": cohorte, "usuario": usuario,
        "entrada_padron": ep, "version_padron": vp, "carrera": carrera,
    }


@pytest.mark.asyncio
async def test_create_calificacion_numeric(db_session, tenant):
    """RED 1.1: Create numeric Calificacion with derived aprobado."""
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=prereqs["entrada_padron"].id,
        actividad="TP1",
        tipo="Numerica",
        nota_numerica=75.00,
        nota_textual=None,
        aprobado=True,
        origen="Importado",
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    assert c.id is not None
    assert isinstance(c.id, uuid.UUID)
    assert c.materia_id == prereqs["materia"].id
    assert c.cohorte_id == prereqs["cohorte"].id
    assert c.entrada_padron_id == prereqs["entrada_padron"].id
    assert c.actividad == "TP1"
    assert c.tipo == "Numerica"
    assert float(c.nota_numerica) == 75.00
    assert c.nota_textual is None
    assert c.aprobado is True
    assert c.origen == "Importado"
    assert c.cargado_por == prereqs["usuario"].id
    assert c.importado_at is not None
    assert c.created_at is not None
    assert c.updated_at is not None
    assert c.deleted_at is None
    assert c.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_create_calificacion_textual(db_session, tenant):
    """TRIANGULATE 1.4: Create textual Calificacion."""
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=prereqs["entrada_padron"].id,
        actividad="Participacion",
        tipo="Textual",
        nota_numerica=None,
        nota_textual="Satisfactorio",
        aprobado=True,
        origen="Manual",
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    assert c.tipo == "Textual"
    assert c.nota_numerica is None
    assert c.nota_textual == "Satisfactorio"
    assert c.aprobado is True
    assert c.origen == "Manual"


@pytest.mark.asyncio
async def test_default_origen_importado(db_session, tenant):
    """TRIANGULATE 1.4: Default origen is Importado."""
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=prereqs["entrada_padron"].id,
        actividad="TP1",
        tipo="Numerica",
        nota_numerica=80.00,
        aprobado=True,
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    await db_session.commit()

    assert c.origen == "Importado"


@pytest.mark.asyncio
async def test_fk_materia_enforced(db_session, tenant):
    """TRIANGULATE 1.4: FK to materia is enforced."""
    fake_id = uuid.uuid4()
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=fake_id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=prereqs["entrada_padron"].id,
        actividad="TP1", tipo="Numerica",
        nota_numerica=80.00, aprobado=True,
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_fk_entrada_padron_enforced(db_session, tenant):
    """TRIANGULATE 1.4: FK to entrada_padron is enforced."""
    fake_id = uuid.uuid4()
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=fake_id,
        actividad="TP1", tipo="Numerica",
        nota_numerica=80.00, aprobado=True,
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_fk_cohorte_enforced(db_session, tenant):
    """TRIANGULATE 1.4: FK to cohorte is enforced."""
    fake_id = uuid.uuid4()
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=fake_id,
        entrada_padron_id=prereqs["entrada_padron"].id,
        actividad="TP1", tipo="Numerica",
        nota_numerica=80.00, aprobado=True,
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_soft_delete_calificacion(db_session, tenant):
    """TRIANGULATE 1.4: Soft delete sets deleted_at."""
    prereqs = await _create_prereqs(db_session, tenant)

    c = Calificacion(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        cohorte_id=prereqs["cohorte"].id,
        entrada_padron_id=prereqs["entrada_padron"].id,
        actividad="TP1", tipo="Numerica",
        nota_numerica=80.00, aprobado=True,
        cargado_por=prereqs["usuario"].id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    c.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    # Query should not find soft-deleted record
    result = await db_session.execute(
        sa.select(Calificacion).where(
            Calificacion.id == c.id,
            Calificacion.deleted_at.is_(None),
        )
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_tenant_isolation_calificacion(db_session, tenant_a, tenant_b):
    """TRIANGULATE 1.4: Tenant isolation for calificacion."""
    pa = await _create_prereqs(db_session, tenant_a)
    pb = await _create_prereqs(db_session, tenant_b)

    ca = Calificacion(
        tenant_id=tenant_a.id,
        materia_id=pa["materia"].id, cohorte_id=pa["cohorte"].id,
        entrada_padron_id=pa["entrada_padron"].id,
        actividad="TP1", tipo="Numerica",
        nota_numerica=80.00, aprobado=True,
        cargado_por=pa["usuario"].id,
    )
    cb = Calificacion(
        tenant_id=tenant_b.id,
        materia_id=pb["materia"].id, cohorte_id=pb["cohorte"].id,
        entrada_padron_id=pb["entrada_padron"].id,
        actividad="TP1", tipo="Numerica",
        nota_numerica=90.00, aprobado=True,
        cargado_por=pb["usuario"].id,
    )
    db_session.add_all([ca, cb])
    await db_session.commit()

    result = await db_session.execute(
        sa.select(Calificacion).where(Calificacion.tenant_id == tenant_a.id)
    )
    items = list(result.scalars().all())
    assert len(items) == 1
    assert items[0].id == ca.id


# ===== Group 2: UmbralMateria Model =====


@pytest.mark.asyncio
async def test_create_umbral_defaults(db_session, tenant):
    """RED 2.1: Create UmbralMateria with default values."""
    prereqs = await _create_prereqs(db_session, tenant)

    um = UmbralMateria(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        asignacion_id=None,
    )
    # Set default for valores_aprobatorios manually since ARRAY(String) may not work in SQLite
    um.valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]
    db_session.add(um)
    await db_session.commit()
    await db_session.refresh(um)

    assert um.id is not None
    assert isinstance(um.id, uuid.UUID)
    assert um.materia_id == prereqs["materia"].id
    assert um.asignacion_id is None
    assert um.umbral_pct == 60
    assert um.created_at is not None
    assert um.updated_at is not None
    assert um.deleted_at is None
    assert um.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_create_umbral_custom_values(db_session, tenant):
    """TRIANGULATE 2.4: Create UmbralMateria with custom values."""
    prereqs = await _create_prereqs(db_session, tenant)

    um = UmbralMateria(
        tenant_id=tenant.id,
        materia_id=prereqs["materia"].id,
        umbral_pct=75,
        asignacion_id=None,
    )
    um.valores_aprobatorios = ["Aprobado", "Promocionado"]
    db_session.add(um)
    await db_session.commit()
    await db_session.refresh(um)

    assert um.umbral_pct == 75


@pytest.mark.asyncio
async def test_fk_umbral_materia_enforced(db_session, tenant):
    """TRIANGULATE 2.4: FK to materia enforced."""
    fake_id = uuid.uuid4()
    um = UmbralMateria(tenant_id=tenant.id, materia_id=fake_id)
    um.valores_aprobatorios = ["Satisfactorio"]
    db_session.add(um)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_soft_delete_umbral(db_session, tenant):
    """TRIANGULATE 2.4: Soft delete on UmbralMateria."""
    prereqs = await _create_prereqs(db_session, tenant)
    um = UmbralMateria(tenant_id=tenant.id, materia_id=prereqs["materia"].id)
    um.valores_aprobatorios = ["Satisfactorio"]
    db_session.add(um)
    await db_session.commit()
    await db_session.refresh(um)

    um.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    result = await db_session.execute(
        sa.select(UmbralMateria).where(
            UmbralMateria.id == um.id,
            UmbralMateria.deleted_at.is_(None),
        )
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_tenant_isolation_umbral(db_session, tenant_a, tenant_b):
    """TRIANGULATE 2.4: Tenant isolation for umbral."""
    pa = await _create_prereqs(db_session, tenant_a)
    pb = await _create_prereqs(db_session, tenant_b)

    ua = UmbralMateria(tenant_id=tenant_a.id, materia_id=pa["materia"].id)
    ua.valores_aprobatorios = ["Satisfactorio"]
    ub = UmbralMateria(tenant_id=tenant_b.id, materia_id=pb["materia"].id)
    ub.valores_aprobatorios = ["Satisfactorio"]
    db_session.add_all([ua, ub])
    await db_session.commit()

    result = await db_session.execute(
        sa.select(UmbralMateria).where(UmbralMateria.tenant_id == tenant_a.id)
    )
    items = list(result.scalars().all())
    assert len(items) == 1
    assert items[0].id == ua.id
