import pytest

from app.core.audit_codes import AuditAction
from app.core.security import decrypt, encrypt
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.schemas.perfil import PerfilUpdateRequest


@pytest.mark.asyncio
async def test_get_perfil_returns_own_data(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="perfil@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Juan",
        apellidos="Perez",
        dni=encrypt("12345678"),
        cuil=encrypt("20-12345678-9"),
        cbu=encrypt("1234567890123456789012"),
    )
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    result = await svc.get_perfil(auth.id, tenant.id)

    assert result.nombre == "Juan"
    assert result.apellidos == "Perez"
    assert result.email == "perfil@test.com"
    assert result.dni == "12345678"
    assert result.cuil == "20-12345678-9"
    assert result.cbu == "1234567890123456789012"
    assert result.facturador is False
    assert result.estado == "Activo"
    assert result.id == u.id


@pytest.mark.asyncio
async def test_update_perfil_nombre(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="update@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="Old", apellidos="Name")
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    req = PerfilUpdateRequest(nombre="Nuevo")
    result = await svc.update_perfil(auth.id, tenant.id, req)

    assert result.nombre == "Nuevo"
    assert result.apellidos == "Name"


@pytest.mark.asyncio
async def test_update_perfil_banco(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="banco@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="B", apellidos="C")
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    req = PerfilUpdateRequest(banco="Galicia")
    result = await svc.update_perfil(auth.id, tenant.id, req)

    assert result.banco == "Galicia"


@pytest.mark.asyncio
async def test_update_perfil_cbu_cifrado_roundtrip(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="cbu@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="X", apellidos="Y")
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    req = PerfilUpdateRequest(cbu="9876543210987654321098")
    await svc.update_perfil(auth.id, tenant.id, req)

    result = await svc.get_perfil(auth.id, tenant.id)
    assert result.cbu == "9876543210987654321098"


@pytest.mark.asyncio
async def test_update_perfil_cuil_no_modificable(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="cuil@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    original_cuil = "20-12345678-9"
    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="C",
        apellidos="D",
        cuil=encrypt(original_cuil),
    )
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    req = PerfilUpdateRequest(nombre="Changed")
    result = await svc.update_perfil(auth.id, tenant.id, req)

    assert result.cuil == original_cuil


@pytest.mark.asyncio
async def test_update_perfil_facturador(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="fact@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="F", apellidos="G")
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    req = PerfilUpdateRequest(facturador=True)
    result = await svc.update_perfil(auth.id, tenant.id, req)

    assert result.facturador is True


@pytest.mark.asyncio
async def test_update_perfil_partial_solo_nombre(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="partial@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Original",
        apellidos="Apellido",
        banco="Santander",
        regional="CABA",
    )
    db_session.add(u)
    await db_session.commit()

    from app.services.perfil_service import PerfilService
    svc = PerfilService(db_session, tenant.id)
    req = PerfilUpdateRequest(nombre="Modificado")
    result = await svc.update_perfil(auth.id, tenant.id, req)

    assert result.nombre == "Modificado"
    assert result.apellidos == "Apellido"
    assert result.banco == "Santander"
    assert result.regional == "CABA"


@pytest.mark.asyncio
async def test_update_perfil_audit(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="auditperfil@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="A", apellidos="B")
    db_session.add(u)
    await db_session.commit()

    from app.repositories.audit_repository import AuditLogRepository
    from app.services.audit_service import AuditService
    from app.services.perfil_service import PerfilService

    audit_repo = AuditLogRepository(db_session, tenant.id)
    audit_svc = AuditService(db_session, audit_repo)
    svc = PerfilService(db_session, tenant.id, audit_svc)
    req = PerfilUpdateRequest(regional="Nordelta")
    await svc.update_perfil(auth.id, tenant.id, req)

    logs = await audit_repo.list(accion=AuditAction.PERFIL_EDITAR.value, limit=5)
    assert len(logs) == 1
    assert logs[0].actor_id == auth.id
