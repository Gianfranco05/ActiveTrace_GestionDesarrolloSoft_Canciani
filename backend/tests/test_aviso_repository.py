import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.asignacion import Asignacion
from app.models.aviso import Aviso
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.rol import Rol
from app.repositories.aviso_repository import AvisoRepository


@pytest.fixture
async def setup_data(db_session, tenant):
    """Create test fixtures: carrera, cohorte, materia, rol, usuarios."""
    carrera = Carrera(
        tenant_id=tenant.id,
        codigo="TEST-CARRERA",
        nombre="Carrera Test",
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre="COHORTE-2026",
        anio=2026,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(cohorte)
    await db_session.flush()

    materia = Materia(
        tenant_id=tenant.id,
        codigo="MAT-TEST",
        nombre="Materia Test",
    )
    db_session.add(materia)
    await db_session.flush()

    rol_profesor = Rol(tenant_id=tenant.id, nombre="PROFESOR")
    db_session.add(rol_profesor)
    await db_session.flush()

    rol_alumno = Rol(tenant_id=tenant.id, nombre="ALUMNO")
    db_session.add(rol_alumno)
    await db_session.flush()

    # Profesor user
    auth_prof = AuthUser(
        tenant_id=tenant.id,
        email="prof@test.com",
        password_hash="pw",
    )
    db_session.add(auth_prof)
    await db_session.flush()
    profesor = Usuario(
        id=auth_prof.id, tenant_id=tenant.id, nombre="Prof", apellidos="Test",
    )
    db_session.add(profesor)
    await db_session.flush()

    # Alumno user
    auth_alum = AuthUser(
        tenant_id=tenant.id,
        email="alum@test.com",
        password_hash="pw",
    )
    db_session.add(auth_alum)
    await db_session.flush()
    alumno = Usuario(
        id=auth_alum.id, tenant_id=tenant.id, nombre="Alum", apellidos="Test",
    )
    db_session.add(alumno)
    await db_session.flush()

    # Profesor assigned to materia and cohorte
    asign_prof_materia = Asignacion(
        tenant_id=tenant.id,
        usuario_id=profesor.id,
        rol_id=rol_profesor.id,
        materia_id=materia.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asign_prof_materia)
    await db_session.flush()

    asign_prof_cohorte = Asignacion(
        tenant_id=tenant.id,
        usuario_id=profesor.id,
        rol_id=rol_profesor.id,
        cohorte_id=cohorte.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asign_prof_cohorte)
    await db_session.flush()

    # Alumno assigned only to cohorte
    asign_alum_cohorte = Asignacion(
        tenant_id=tenant.id,
        usuario_id=alumno.id,
        rol_id=rol_alumno.id,
        cohorte_id=cohorte.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asign_alum_cohorte)
    await db_session.flush()

    await db_session.commit()

    return {
        "tenant": tenant,
        "carrera": carrera,
        "cohorte": cohorte,
        "materia": materia,
        "rol_profesor": rol_profesor,
        "rol_alumno": rol_alumno,
        "profesor": profesor,
        "alumno": alumno,
    }


@pytest.mark.asyncio
async def test_list_visibles_global_visible_to_all(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Global",
        cuerpo="Visible para todos",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    profesor_items, profesor_total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert profesor_total == 1
    assert profesor_items[0].id == aviso.id

    alumno_items, alumno_total = await repo.list_visibles(
        setup_data["alumno"].id, 0, 10,
    )
    assert alumno_total == 1


@pytest.mark.asyncio
async def test_list_visibles_por_materia_only_assigned(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="PorMateria",
        materia_id=setup_data["materia"].id,
        severidad="Info",
        titulo="Aviso Materia",
        cuerpo="Solo para asignados a la materia",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    profesor_items, profesor_total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert profesor_total == 1
    assert profesor_items[0].id == aviso.id

    alumno_items, alumno_total = await repo.list_visibles(
        setup_data["alumno"].id, 0, 10,
    )
    assert alumno_total == 0


@pytest.mark.asyncio
async def test_list_visibles_por_cohorte_only_assigned(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="PorCohorte",
        cohorte_id=setup_data["cohorte"].id,
        severidad="Info",
        titulo="Aviso Cohorte",
        cuerpo="Solo para la cohorte",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    profesor_items, profesor_total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert profesor_total == 1

    alumno_items, alumno_total = await repo.list_visibles(
        setup_data["alumno"].id, 0, 10,
    )
    assert alumno_total == 1


@pytest.mark.asyncio
async def test_list_visibles_por_rol_only_matching(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="PorRol",
        rol_destino="PROFESOR",
        severidad="Info",
        titulo="Aviso Profesores",
        cuerpo="Solo para profesores",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    profesor_items, profesor_total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert profesor_total == 1
    assert profesor_items[0].id == aviso.id

    alumno_items, alumno_total = await repo.list_visibles(
        setup_data["alumno"].id, 0, 10,
    )
    assert alumno_total == 0


@pytest.mark.asyncio
async def test_list_visibles_fuera_vigencia_not_visible(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Futuro",
        cuerpo="No visible aún",
        inicio_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2031, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    profesor_items, profesor_total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert profesor_total == 0


@pytest.mark.asyncio
async def test_list_visibles_soft_deleted_not_visible(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Borrado",
        cuerpo="No debería verse",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    aviso.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    items, total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total == 0


@pytest.mark.asyncio
async def test_list_visibles_inactive_not_visible(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Inactivo",
        cuerpo="No activo",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        activo=False,
    )
    db_session.add(aviso)
    await db_session.commit()

    items, total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total == 0


@pytest.mark.asyncio
async def test_list_visibles_ack_excluded_if_confirmed(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso con Ack",
        cuerpo="Requiere confirmación",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    # Before ack, visible
    items_before, total_before = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total_before == 1

    ack = AcknowledgmentAviso(
        aviso_id=aviso.id,
        usuario_id=setup_data["profesor"].id,
    )
    db_session.add(ack)
    await db_session.commit()

    # After ack, excluded
    items_after, total_after = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total_after == 0


@pytest.mark.asyncio
async def test_list_visibles_order_by_prioridad(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    aviso_a = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="A",
        cuerpo="A",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        orden=10,
    )
    aviso_b = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="B",
        cuerpo="B",
        inicio_en=datetime(2026, 6, 3, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        orden=5,
    )
    aviso_c = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="C",
        cuerpo="C",
        inicio_en=datetime(2026, 5, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        orden=10,
    )
    db_session.add_all([aviso_a, aviso_b, aviso_c])
    await db_session.commit()

    items, total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total == 3
    # orden 10 first, then by inicio_en desc
    assert items[0].id == aviso_a.id  # orden=10, inicio_en=2026-06-01
    assert items[1].id == aviso_c.id  # orden=10, inicio_en=2026-05-01
    assert items[2].id == aviso_b.id  # orden=5


@pytest.mark.asyncio
async def test_list_visibles_admin_sees_future_aviso(db_session, tenant, setup_data):
    """Admin mode should show avisos outside vigencia (future)."""
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Futuro Admin",
        cuerpo="Debería verse en admin",
        inicio_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2031, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    # Without admin, not visible
    items_normal, total_normal = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total_normal == 0

    # With admin, visible
    items_admin, total_admin = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True,
    )
    assert total_admin == 1
    assert items_admin[0].id == aviso.id


@pytest.mark.asyncio
async def test_list_visibles_admin_sees_inactive(db_session, tenant, setup_data):
    """Admin mode should show inactive avisos."""
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Inactivo Admin",
        cuerpo="Debería verse en admin",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        activo=False,
    )
    db_session.add(aviso)
    await db_session.commit()

    items_admin, total_admin = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True,
    )
    assert total_admin == 1
    assert items_admin[0].id == aviso.id


@pytest.mark.asyncio
async def test_list_visibles_admin_sees_ack_confirmed(db_session, tenant, setup_data):
    """Admin mode should show avisos even if already acknowledged."""
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso con Ack Admin",
        cuerpo="Debería verse en admin aunque tenga ack",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.commit()

    ack = AcknowledgmentAviso(
        aviso_id=aviso.id,
        usuario_id=setup_data["profesor"].id,
    )
    db_session.add(ack)
    await db_session.commit()

    # Normal mode excludes it
    items_normal, total_normal = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10,
    )
    assert total_normal == 0

    # Admin mode includes it
    items_admin, total_admin = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True,
    )
    assert total_admin == 1
    assert items_admin[0].id == aviso.id


@pytest.mark.asyncio
async def test_list_visibles_admin_excludes_soft_deleted(db_session, tenant, setup_data):
    """Admin mode should still exclude soft-deleted avisos."""
    repo = AvisoRepository(db_session, tenant.id)

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Aviso Borrado Admin",
        cuerpo="No debería verse ni en admin",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    aviso.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    items_admin, total_admin = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True,
    )
    assert total_admin == 0


@pytest.mark.asyncio
async def test_list_visibles_admin_respects_activo_filter(db_session, tenant, setup_data):
    """Admin mode should still filter by activo when explicitly set."""
    repo = AvisoRepository(db_session, tenant.id)

    aviso_active = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Activo",
        cuerpo="Activo",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        activo=True,
    )
    aviso_inactive = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Inactivo",
        cuerpo="Inactivo",
        inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
        fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        activo=False,
    )
    db_session.add_all([aviso_active, aviso_inactive])
    await db_session.commit()

    items_all, total_all = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True,
    )
    assert total_all == 2

    items_active, total_active = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True, activo=True,
    )
    assert total_active == 1
    assert items_active[0].id == aviso_active.id

    items_inactive, total_inactive = await repo.list_visibles(
        setup_data["profesor"].id, 0, 10, admin=True, activo=False,
    )
    assert total_inactive == 1
    assert items_inactive[0].id == aviso_inactive.id


@pytest.mark.asyncio
async def test_list_visibles_pagination(db_session, tenant, setup_data):
    repo = AvisoRepository(db_session, tenant.id)

    for i in range(5):
        aviso = Aviso(
            tenant_id=tenant.id,
            alcance="Global",
            severidad="Info",
            titulo=f"Aviso {i}",
            cuerpo=f"Cuerpo {i}",
            inicio_en=datetime(2020, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
            orden=i,
        )
        db_session.add(aviso)
    await db_session.commit()

    items, total = await repo.list_visibles(
        setup_data["profesor"].id, 0, 2,
    )
    assert total == 5
    assert len(items) == 2

    items, total = await repo.list_visibles(
        setup_data["profesor"].id, 2, 2,
    )
    assert total == 5
    assert len(items) == 2
