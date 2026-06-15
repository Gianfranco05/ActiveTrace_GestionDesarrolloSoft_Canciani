"""Tests: Tenant config, permission seeding, audit code registration."""

import uuid

import pytest
from sqlalchemy import select

from app.core.audit_codes import AuditAction
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_tenant_has_requiere_aprobacion_comunicaciones(db_session, tenant):
    t = await db_session.get(Tenant, tenant.id)
    assert hasattr(t, "requiere_aprobacion_comunicaciones")
    assert t.requiere_aprobacion_comunicaciones is False


@pytest.mark.asyncio
async def test_tenant_flag_can_be_set_true(db_session):
    tenant = Tenant(name="Flag Test Tenant", slug="flag-test-tenant")
    db_session.add(tenant)
    await db_session.flush()

    tenant.requiere_aprobacion_comunicaciones = True
    await db_session.commit()
    await db_session.refresh(tenant)

    assert tenant.requiere_aprobacion_comunicaciones is True


@pytest.mark.asyncio
async def test_seed_comunicacion_enviar_permiso(db_session, tenant):
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="comunicacion:enviar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()

    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == "comunicacion:enviar"),
    )
    permiso = result.scalar_one()
    assert permiso.codigo == "comunicacion:enviar"

    rp_result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == rol.id,
            RolPermiso.permiso_id == permiso.id,
        ),
    )
    assert rp_result.scalar_one() is not None


@pytest.mark.asyncio
async def test_seed_comunicacion_aprobar_permiso(db_session, tenant):
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="comunicacion:aprobar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()

    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == "comunicacion:aprobar"),
    )
    assert result.scalar_one() is not None


@pytest.mark.asyncio
async def test_seed_comunicacion_ver_permiso(db_session, tenant):
    p = Permiso(codigo="comunicacion:ver")
    db_session.add(p)
    await db_session.commit()

    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == "comunicacion:ver"),
    )
    assert result.scalar_one() is not None


def test_audit_codes_registered():
    assert AuditAction.COMUNICACION_PREVIEW == "COMUNICACION_PREVIEW"
    assert AuditAction.COMUNICACION_ENVIAR == "COMUNICACION_ENVIAR"
    assert AuditAction.COMUNICACION_APROBAR == "COMUNICACION_APROBAR"
    assert AuditAction.COMUNICACION_CANCELAR == "COMUNICACION_CANCELAR"
