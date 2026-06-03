from datetime import date, timedelta, datetime, timezone

from app.services.role_resolver import RoleResolver
from app.models.rol import Rol
from app.models.asignacion import Asignacion
from app.models.usuario import Usuario


async def test_resolve_roles_returns_role_names(db_session, tenant):
    r = Rol(tenant_id=tenant.id, nombre="Tesorero")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    uu = Usuario(tenant_id=tenant.id, nombre="X", apellidos="Y")
    db_session.add(uu)
    await db_session.commit()
    await db_session.refresh(uu)

    a = Asignacion(tenant_id=tenant.id, usuario_id=uu.id, rol_id=r.id, vig_desde=date.today())
    db_session.add(a)
    await db_session.commit()

    resolver = RoleResolver(db_session, tenant.id)
    roles = await resolver.resolve_roles(uu.id)
    assert "Tesorero" in roles


async def test_resolve_roles_empty_no_assignments(db_session, tenant):
    uu = Usuario(tenant_id=tenant.id, nombre="Empty", apellidos="Roles")
    db_session.add(uu)
    await db_session.commit()
    await db_session.refresh(uu)

    resolver = RoleResolver(db_session, tenant.id)
    roles = await resolver.resolve_roles(uu.id)
    assert roles == []


async def test_resolve_roles_excludes_expired(db_session, tenant):
    r = Rol(tenant_id=tenant.id, nombre="Vencido")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    uu = Usuario(tenant_id=tenant.id, nombre="Exp", apellidos="User")
    db_session.add(uu)
    await db_session.commit()
    await db_session.refresh(uu)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=uu.id,
        rol_id=r.id,
        vig_desde=date.today() - timedelta(days=30),
        vig_hasta=date.today() - timedelta(days=1),
    )
    db_session.add(a)
    await db_session.commit()

    resolver = RoleResolver(db_session, tenant.id)
    roles = await resolver.resolve_roles(uu.id)
    assert "Vencido" in roles


async def test_resolve_roles_excludes_soft_deleted_asignacion(db_session, tenant):
    r = Rol(tenant_id=tenant.id, nombre="SoftDelAsig")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    uu = Usuario(tenant_id=tenant.id, nombre="Soft", apellidos="DelAsig")
    db_session.add(uu)
    await db_session.commit()
    await db_session.refresh(uu)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=uu.id,
        rol_id=r.id,
        vig_desde=date.today(),
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    a.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    resolver = RoleResolver(db_session, tenant.id)
    roles = await resolver.resolve_roles(uu.id)
    assert "SoftDelAsig" not in roles


async def test_resolve_roles_excludes_soft_deleted_rol(db_session, tenant):
    r = Rol(tenant_id=tenant.id, nombre="SoftDelRol")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    uu = Usuario(tenant_id=tenant.id, nombre="Soft", apellidos="DelRol")
    db_session.add(uu)
    await db_session.commit()
    await db_session.refresh(uu)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=uu.id,
        rol_id=r.id,
        vig_desde=date.today(),
    )
    db_session.add(a)
    await db_session.commit()

    r.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    resolver = RoleResolver(db_session, tenant.id)
    roles = await resolver.resolve_roles(uu.id)
    assert "SoftDelRol" not in roles


async def test_resolve_roles_returns_distinct(db_session, tenant):
    r1 = Rol(tenant_id=tenant.id, nombre="Profesor")
    db_session.add(r1)
    await db_session.commit()
    await db_session.refresh(r1)

    uu = Usuario(tenant_id=tenant.id, nombre="Distinct", apellidos="Roles")
    db_session.add(uu)
    await db_session.commit()
    await db_session.refresh(uu)

    for _ in range(3):
        a = Asignacion(
            tenant_id=tenant.id,
            usuario_id=uu.id,
            rol_id=r1.id,
            vig_desde=date.today(),
        )
        db_session.add(a)
    await db_session.commit()

    resolver = RoleResolver(db_session, tenant.id)
    roles = await resolver.resolve_roles(uu.id)
    assert len(roles) == 1
    assert roles == ["Profesor"]
