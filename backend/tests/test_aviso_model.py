import uuid
from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_create_aviso(db_session, tenant):
    from app.models.aviso import Aviso

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Bienvenida",
        cuerpo="Bienvenidos al cuatrimestre",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()
    await db_session.refresh(aviso)

    assert aviso.id is not None
    assert aviso.tenant_id == tenant.id
    assert aviso.alcance == "Global"
    assert aviso.activo is True
    assert aviso.requiere_ack is False
    assert aviso.orden == 0
    assert aviso.created_at is not None


@pytest.mark.asyncio
async def test_create_aviso_with_ack_true(db_session, tenant):
    from app.models.aviso import Aviso

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Critico",
        titulo="Urgente",
        cuerpo="Mensaje urgente",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
        requiere_ack=True,
        orden=10,
    )
    db_session.add(aviso)
    await db_session.commit()
    await db_session.refresh(aviso)

    assert aviso.requiere_ack is True
    assert aviso.orden == 10


@pytest.mark.asyncio
async def test_create_acknowledgment_aviso(db_session, tenant):
    from app.models.aviso import Aviso
    from app.models.acknowledgment_aviso import AcknowledgmentAviso
    from app.models.usuario import Usuario
    from app.models.auth_user import AuthUser

    auth = AuthUser(
        tenant_id=tenant.id,
        email="ack_test@test.com",
        password_hash="pw",
    )
    db_session.add(auth)
    await db_session.flush()

    usuario = Usuario(
        id=auth.id, tenant_id=tenant.id, nombre="Test", apellidos="User",
    )
    db_session.add(usuario)
    await db_session.flush()

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Test",
        cuerpo="Cuerpo",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.flush()

    ack = AcknowledgmentAviso(
        aviso_id=aviso.id,
        usuario_id=usuario.id,
    )
    db_session.add(ack)
    await db_session.commit()
    await db_session.refresh(ack)

    assert ack.id is not None
    assert ack.aviso_id == aviso.id
    assert ack.usuario_id == usuario.id
    assert ack.confirmado_at is not None


@pytest.mark.asyncio
async def test_acknowledgment_unique_constraint(db_session, tenant):
    from app.models.aviso import Aviso
    from app.models.acknowledgment_aviso import AcknowledgmentAviso
    from app.models.usuario import Usuario
    from app.models.auth_user import AuthUser

    auth = AuthUser(
        tenant_id=tenant.id,
        email="ack_unique@test.com",
        password_hash="pw",
    )
    db_session.add(auth)
    await db_session.flush()

    usuario = Usuario(
        id=auth.id, tenant_id=tenant.id, nombre="Test", apellidos="User",
    )
    db_session.add(usuario)
    await db_session.flush()

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Test",
        cuerpo="Cuerpo",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.flush()

    ack1 = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=usuario.id)
    db_session.add(ack1)
    await db_session.commit()

    ack2 = AcknowledgmentAviso(aviso_id=aviso.id, usuario_id=usuario.id)
    db_session.add(ack2)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_aviso_soft_delete(db_session, tenant):
    from app.models.aviso import Aviso

    aviso = Aviso(
        tenant_id=tenant.id,
        alcance="Global",
        severidad="Info",
        titulo="Para borrar",
        cuerpo="Será soft-delete",
        inicio_en=datetime(2026, 6, 1, tzinfo=timezone.utc),
        fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db_session.add(aviso)
    await db_session.commit()

    aviso.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(aviso)

    assert aviso.deleted_at is not None
