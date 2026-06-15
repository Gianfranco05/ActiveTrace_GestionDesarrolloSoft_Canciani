import uuid

import pytest

from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.repositories.rbac_repository import RbacRepository


@pytest.fixture
def repo():
    return RbacRepository()


async def _seed_role_perms(session, tenant_id: uuid.UUID):
    roles = {
        "ADMIN": Rol(nombre="ADMIN", tenant_id=tenant_id),
        "PROFESOR": Rol(nombre="PROFESOR", tenant_id=tenant_id),
        "ALUMNO": Rol(nombre="ALUMNO", tenant_id=tenant_id),
    }
    for r in roles.values():
        session.add(r)
    await session.commit()
    for r in roles.values():
        await session.refresh(r)

    perms = {
        "importar": Permiso(codigo="calificaciones:importar"),
        "ver_estado": Permiso(codigo="estado_academico:ver"),
        "reservar": Permiso(codigo="evaluacion:reservar"),
        "auditar": Permiso(codigo="auditoria:ver"),
    }
    for p in perms.values():
        session.add(p)
    await session.commit()
    for p in perms.values():
        await session.refresh(p)

    rps = [
        RolPermiso(rol_id=roles["ADMIN"].id, permiso_id=perms["importar"].id),
        RolPermiso(rol_id=roles["ADMIN"].id, permiso_id=perms["auditar"].id),
        RolPermiso(rol_id=roles["PROFESOR"].id, permiso_id=perms["importar"].id),
        RolPermiso(rol_id=roles["ALUMNO"].id, permiso_id=perms["ver_estado"].id),
        RolPermiso(rol_id=roles["ALUMNO"].id, permiso_id=perms["reservar"].id),
    ]
    for rp in rps:
        session.add(rp)
    await session.commit()

    return roles, perms


@pytest.mark.asyncio
async def test_get_effective_permissions(db_session, tenant):
    roles, perms = await _seed_role_perms(db_session, tenant.id)

    admin_perms = await RbacRepository.get_effective_permissions(
        db_session, ["ADMIN"],
    )
    assert "calificaciones:importar" in admin_perms
    assert "auditoria:ver" in admin_perms
    assert "estado_academico:ver" not in admin_perms
    assert len(admin_perms) == 2

    alumno_perms = await RbacRepository.get_effective_permissions(
        db_session, ["ALUMNO"],
    )
    assert "estado_academico:ver" in alumno_perms
    assert "evaluacion:reservar" in alumno_perms
    assert "calificaciones:importar" not in alumno_perms
    assert len(alumno_perms) == 2


@pytest.mark.asyncio
async def test_empty_role_list_returns_empty(db_session):
    result = await RbacRepository.get_effective_permissions(db_session, [])
    assert result == set()


@pytest.mark.asyncio
async def test_non_existent_role_returns_empty(db_session):
    result = await RbacRepository.get_effective_permissions(
        db_session, ["NONEXISTENT"],
    )
    assert result == set()


@pytest.mark.asyncio
async def test_get_roles_by_tenant(db_session, tenant_a, tenant_b):
    r1 = Rol(nombre="TENANT_A_ROLE", tenant_id=tenant_a.id)
    r2 = Rol(nombre="TENANT_B_ROLE", tenant_id=tenant_b.id)
    db_session.add_all([r1, r2])
    await db_session.commit()

    roles_a = await RbacRepository.get_roles_by_tenant(db_session, tenant_a.id)
    assert len(roles_a) == 1
    assert roles_a[0].nombre == "TENANT_A_ROLE"

    roles_b = await RbacRepository.get_roles_by_tenant(db_session, tenant_b.id)
    assert len(roles_b) == 1
    assert roles_b[0].nombre == "TENANT_B_ROLE"


@pytest.mark.asyncio
async def test_get_roles_by_tenant_excludes_soft_deleted(db_session, tenant):
    from datetime import datetime, timezone

    r1 = Rol(nombre="ACTIVE", tenant_id=tenant.id)
    r2 = Rol(nombre="DELETED", tenant_id=tenant.id)
    db_session.add_all([r1, r2])
    await db_session.commit()

    r2.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    roles = await RbacRepository.get_roles_by_tenant(db_session, tenant.id)
    assert len(roles) == 1
    assert roles[0].nombre == "ACTIVE"


@pytest.mark.asyncio
async def test_assign_permisos_replace_all(db_session, tenant):
    rol = Rol(nombre="ASSIGN_TEST", tenant_id=tenant.id)
    db_session.add(rol)
    p1 = Permiso(codigo="perm:one")
    p2 = Permiso(codigo="perm:two")
    p3 = Permiso(codigo="perm:three")
    db_session.add_all([p1, p2, p3])
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p1)
    await db_session.refresh(p2)

    # Assign p1 and p2
    await RbacRepository.assign_permisos_to_rol(
        db_session, rol.id, [p1.id, p2.id],
    )

    perms = await RbacRepository.get_effective_permissions(
        db_session, ["ASSIGN_TEST"],
    )
    assert perms == {"perm:one", "perm:two"}

    # Replace with p2 and p3
    await RbacRepository.assign_permisos_to_rol(
        db_session, rol.id, [p2.id, p3.id],
    )

    perms = await RbacRepository.get_effective_permissions(
        db_session, ["ASSIGN_TEST"],
    )
    assert perms == {"perm:two", "perm:three"}
