import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.repositories.rbac_repository import RbacRepository
from app.schemas.rbac import (
    PermisoCreate,
    PermisoResponse,
    RolCreate,
    RolNameResponse,
    RolResponse,
    RolUpdate,
    RolWithPermisosResponse,
    SetRolePermisosRequest,
)

router = APIRouter(prefix="/api/v1/rbac", tags=["rbac"])


@router.get("/roles-names", response_model=list[RolNameResponse])
async def list_role_names(
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight endpoint for dropdowns — returns {id, nombre} for all tenant roles."""
    roles = await RbacRepository.get_roles_by_tenant(db, current_user.tenant_id)
    return [RolNameResponse.model_validate(r) for r in roles]


@router.get("/roles", response_model=list[RolResponse])
async def list_roles(
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    roles = await RbacRepository.get_roles_by_tenant(db, current_user.tenant_id)
    return roles


@router.post("/roles", response_model=RolResponse, status_code=201)
async def create_role(
    body: RolCreate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    rol = Rol(
        nombre=body.nombre,
        descripcion=body.descripcion,
        tenant_id=current_user.tenant_id,
    )
    db.add(rol)
    try:
        await db.commit()
        await db.refresh(rol)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Role name already exists for this tenant") from None
    return rol


@router.get("/roles/{rol_id}", response_model=RolWithPermisosResponse)
async def get_role(
    rol_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Rol).where(
        Rol.id == rol_id,
        Rol.tenant_id == current_user.tenant_id,
        Rol.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=404, detail="Role not found")

    perms = await RbacRepository.get_effective_permissions(db, [rol.nombre])
    return RolWithPermisosResponse(
        id=rol.id,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        permisos=sorted(perms),
    )


@router.put("/roles/{rol_id}", response_model=RolResponse)
async def update_role(
    rol_id: uuid.UUID,
    body: RolUpdate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Rol).where(
        Rol.id == rol_id,
        Rol.tenant_id == current_user.tenant_id,
        Rol.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=404, detail="Role not found")

    if body.nombre is not None:
        rol.nombre = body.nombre
    if body.descripcion is not None:
        rol.descripcion = body.descripcion

    try:
        await db.commit()
        await db.refresh(rol)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Role name already exists for this tenant") from None
    return rol


@router.put("/roles/{rol_id}/permisos", response_model=RolWithPermisosResponse)
async def set_role_permisos(
    rol_id: uuid.UUID,
    body: SetRolePermisosRequest,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Rol).where(
        Rol.id == rol_id,
        Rol.tenant_id == current_user.tenant_id,
        Rol.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    rol = result.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=404, detail="Role not found")

    await RbacRepository.assign_permisos_to_rol(db, rol_id, body.permiso_ids)

    perms = await RbacRepository.get_effective_permissions(db, [rol.nombre])
    return RolWithPermisosResponse(
        id=rol.id,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        permisos=sorted(perms),
    )


@router.get("/permisos", response_model=list[PermisoResponse])
async def list_permisos(
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    return await RbacRepository.get_permisos_catalog(db)


@router.post("/permisos", response_model=PermisoResponse, status_code=201)
async def create_permiso(
    body: PermisoCreate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    permiso = Permiso(codigo=body.codigo, descripcion=body.descripcion)
    db.add(permiso)
    try:
        await db.commit()
        await db.refresh(permiso)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Permission code already exists") from None
    return permiso
