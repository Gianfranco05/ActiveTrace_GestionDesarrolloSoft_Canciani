"""TDD: AsignacionService — overlap enforcement."""

import uuid
from datetime import date

import pytest

from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.repositories.asignacion_repository import AsignacionRepository
from app.services.asignacion_service import AsignacionService
from app.schemas.asignaciones import AsignacionCreate
from app.core.security import hash_password


async def _create_usuario(db_session, tenant, email):
    auth_user = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("Secure123"),
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)
    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="AsigSvc",
        apellidos="Test",
        dni="dni",
        cuil="cuil",
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


@pytest.fixture
def asig_service(db_session, tenant):
    repo = AsignacionRepository(db_session, tenant.id)
    return AsignacionService(repo)


@pytest.mark.asyncio
async def test_create_asignacion_succeeds(db_session, tenant, asig_service):
    usuario = await _create_usuario(db_session, tenant, "asig_svc_create@test.com")
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    result = await asig_service.create(AsignacionCreate(
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2026, 1, 1),
    ))
    assert result.id is not None
    assert result.usuario_id == usuario.id


@pytest.mark.asyncio
async def test_create_non_overlapping_vigencia_succeeds(db_session, tenant, asig_service):
    usuario = await _create_usuario(db_session, tenant, "non_overlap@test.com")
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    await asig_service.create(AsignacionCreate(
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2024, 1, 1),
        vig_hasta=date(2024, 6, 30),
    ))
    result = await asig_service.create(AsignacionCreate(
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2024, 7, 1),
        vig_hasta=date(2024, 12, 31),
    ))
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_overlapping_vigencia_raises_409(db_session, tenant, asig_service):
    usuario = await _create_usuario(db_session, tenant, "overlap_test@test.com")
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    await asig_service.create(AsignacionCreate(
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2024, 1, 1),
        vig_hasta=date(2024, 12, 31),
    ))
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await asig_service.create(AsignacionCreate(
            usuario_id=usuario.id,
            rol_id=rol.id,
            vig_desde=date(2024, 6, 1),
            vig_hasta=date(2024, 9, 30),
        ))
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_references_nonexistent_usuario_raises_404(
    db_session, tenant, asig_service,
):
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await asig_service.create(AsignacionCreate(
            usuario_id=uuid.uuid4(),
            rol_id=rol.id,
            vig_desde=date(2026, 1, 1),
        ))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_references_nonexistent_rol_raises_404(db_session, tenant, asig_service):
    # Triangulation: missing rol should raise 404 like usuario
    usuario = await _create_usuario(db_session, tenant, "triangulate_rol@test.com")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await asig_service.create(AsignacionCreate(
            usuario_id=usuario.id,
            rol_id=uuid.uuid4(),
            vig_desde=date(2026, 1, 1),
        ))
    assert exc.value.status_code == 404
