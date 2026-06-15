import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.audit_log import AuditLog
from app.models.auth_user import AuthUser
from app.repositories.audit_repository import AuditLogRepository


@pytest.mark.asyncio
async def test_count_by_day_groups_correctly(db_session, tenant):
    user = AuthUser(tenant_id=tenant.id, email="daycount@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)

    e1 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="LOGIN",
                  fecha_hora=yesterday)
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="LOGOUT",
                  fecha_hora=today)
    e3 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="QUERY",
                  fecha_hora=today)
    db_session.add_all([e1, e2, e3])
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.count_by_day(
        fecha_desde=yesterday - timedelta(days=1),
        fecha_hasta=today + timedelta(days=1),
    )

    assert len(result) == 2
    sorted_result = sorted(result, key=lambda r: str(r["dia"]))
    assert sorted_result[0]["total_acciones"] == 1
    assert sorted_result[1]["total_acciones"] == 2


@pytest.mark.asyncio
async def test_count_by_day_empty_range(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.count_by_day(
        fecha_desde=datetime.now(timezone.utc) - timedelta(days=10),
        fecha_hasta=datetime.now(timezone.utc),
    )
    assert result == []


@pytest.mark.asyncio
async def test_count_by_day_with_actor_id_filter(db_session, tenant):
    user_a = AuthUser(tenant_id=tenant.id, email="actor_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="actor_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    today = datetime.now(timezone.utc)
    e1 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, accion="LOGIN",
                  fecha_hora=today)
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, accion="LOGIN",
                  fecha_hora=today)
    db_session.add_all([e1, e2])
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.count_by_day(
        fecha_desde=today - timedelta(days=1),
        fecha_hasta=today + timedelta(days=1),
        actor_id=user_a.id,
    )
    assert len(result) == 1
    assert result[0]["total_acciones"] == 1


@pytest.mark.asyncio
async def test_count_by_actor_materia_accion_groups_correctly(db_session, tenant):
    user = AuthUser(tenant_id=tenant.id, email="groupby@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    materia_id = uuid.uuid4()
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)

    e1 = AuditLog(tenant_id=tenant.id, actor_id=user.id, materia_id=materia_id,
                  accion="CALIFICACIONES_CARGAR", fecha_hora=yesterday)
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user.id, materia_id=materia_id,
                  accion="CALIFICACIONES_CARGAR", fecha_hora=today)
    e3 = AuditLog(tenant_id=tenant.id, actor_id=user.id, materia_id=materia_id,
                  accion="PADRON_CARGAR", fecha_hora=today)
    db_session.add_all([e1, e2, e3])
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.count_by_actor_materia_accion(
        fecha_desde=yesterday - timedelta(days=1),
        fecha_hasta=today + timedelta(days=1),
    )

    assert len(result) == 2
    totals = {r["accion"]: r["cantidad"] for r in result}
    assert totals["CALIFICACIONES_CARGAR"] == 2
    assert totals["PADRON_CARGAR"] == 1


@pytest.mark.asyncio
async def test_count_by_actor_materia_accion_empty(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.count_by_actor_materia_accion(
        fecha_desde=datetime.now(timezone.utc) - timedelta(days=10),
        fecha_hasta=datetime.now(timezone.utc),
    )
    assert result == []


@pytest.mark.asyncio
async def test_list_with_join_resolves_names(db_session, tenant):
    from app.models.usuario import Usuario
    from app.models.materia import Materia

    user = AuthUser(tenant_id=tenant.id, email="joinres@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    profile = Usuario(tenant_id=tenant.id, id=user.id, nombre="Juan", apellidos="Pérez")
    db_session.add(profile)

    mat = Materia(tenant_id=tenant.id, codigo="MAT101", nombre="Matemática I")
    db_session.add(mat)
    await db_session.commit()

    today = datetime.now(timezone.utc)
    entry = AuditLog(tenant_id=tenant.id, actor_id=user.id, materia_id=mat.id,
                     accion="CONSULTA", fecha_hora=today)
    db_session.add(entry)
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.list_with_join(
        fecha_desde=today - timedelta(days=1),
        fecha_hasta=today + timedelta(days=1),
    )

    assert len(result) == 1
    row = result[0]
    assert row["actor_nombre"] == "Juan Pérez"
    assert row["materia_nombre"] == "Matemática I"
    assert row["accion"] == "CONSULTA"


@pytest.mark.asyncio
async def test_list_with_join_null_names_on_missing_relations(db_session, tenant):
    user = AuthUser(tenant_id=tenant.id, email="nullnames@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    unknown_materia_id = uuid.uuid4()
    today = datetime.now(timezone.utc)
    entry = AuditLog(tenant_id=tenant.id, actor_id=user.id, materia_id=unknown_materia_id,
                     accion="CONSULTA", fecha_hora=today)
    db_session.add(entry)
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)
    result = await repo.list_with_join(
        fecha_desde=today - timedelta(days=1),
        fecha_hasta=today + timedelta(days=1),
    )

    assert len(result) == 1
    row = result[0]
    assert row["actor_nombre"] is None
    assert row["materia_nombre"] is None


@pytest.mark.asyncio
async def test_list_with_join_filters(db_session, tenant):
    from app.models.usuario import Usuario
    from app.models.materia import Materia

    user_a = AuthUser(tenant_id=tenant.id, email="filterA@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="filterB@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    profile_a = Usuario(tenant_id=tenant.id, id=user_a.id, nombre="Ana", apellidos="López")
    profile_b = Usuario(tenant_id=tenant.id, id=user_b.id, nombre="Ben", apellidos="Díaz")
    db_session.add_all([profile_a, profile_b])

    mat_a = Materia(tenant_id=tenant.id, codigo="A101", nombre="Álgebra")
    mat_b = Materia(tenant_id=tenant.id, codigo="B202", nombre="Biología")
    db_session.add_all([mat_a, mat_b])
    await db_session.commit()

    today = datetime.now(timezone.utc)
    e1 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat_a.id,
                  accion="CALIFICAR", fecha_hora=today, ip="192.168.1.1")
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat_b.id,
                  accion="EXPORTAR", fecha_hora=today, ip="10.0.0.5")
    db_session.add_all([e1, e2])
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)

    result = await repo.list_with_join(usuario_id=user_a.id)
    assert len(result) == 1
    assert result[0]["accion"] == "CALIFICAR"

    result = await repo.list_with_join(materia_id=mat_b.id)
    assert len(result) == 1
    assert result[0]["accion"] == "EXPORTAR"

    result = await repo.list_with_join(ip="192.168")
    assert len(result) == 1
    assert result[0]["actor_nombre"] == "Ana López"

    result = await repo.list_with_join(accion="EXPORTAR")
    assert len(result) == 1
    assert result[0]["actor_nombre"] == "Ben Díaz"


@pytest.mark.asyncio
async def test_count_with_filters_matches_filters(db_session, tenant):
    user = AuthUser(tenant_id=tenant.id, email="countf@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    today = datetime.now(timezone.utc)
    e1 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="LOGIN",
                  fecha_hora=today, ip="10.0.0.1")
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="LOGOUT",
                  fecha_hora=today, ip="192.168.1.1")
    db_session.add_all([e1, e2])
    await db_session.commit()

    repo = AuditLogRepository(db_session, tenant.id)

    total = await repo.count_with_filters()
    assert total == 2

    total = await repo.count_with_filters(accion="LOGIN")
    assert total == 1

    total = await repo.count_with_filters(ip="10.0")
    assert total == 1

    total = await repo.count_with_filters(usuario_id=user.id)
    assert total == 2

    other_uuid = uuid.uuid4()
    total = await repo.count_with_filters(usuario_id=other_uuid)
    assert total == 0
