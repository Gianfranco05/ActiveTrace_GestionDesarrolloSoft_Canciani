"""Usuario router — CRUD with PII-safe responses."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.core.security import hash_password
from app.models.asignacion import Asignacion
from app.models.auth_user import AuthUser
from app.models.rol import Rol
from app.repositories.auth_repository import AuthRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.common import ListResponse
from app.schemas.usuarios import (
    AdminResetPasswordRequest,
    EstadoToggleRequest,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioSafeResponse,
    UsuarioUpdate,
)
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api/v1/admin/usuarios", tags=["usuarios"])


@router.get("", response_model=ListResponse[UsuarioSafeResponse])
async def list_usuarios(
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
    rol: str | None = Query(None),
    activo: bool | None = Query(None),
    busqueda: str | None = Query(None),
):
    repo = UsuarioRepository(db, current_user.tenant_id)
    service = UsuarioService(repo, db)
    items = await service.list()

    # Apply filters
    if activo is not None:
        items = [u for u in items if u.activo == activo]
    if busqueda:
        q = busqueda.lower()
        items = [u for u in items if q in (u.nombre or "").lower() or q in (u.apellidos or "").lower()]

    # Resolve email (from AuthUser) and roles (from Asignacion) in batch
    user_ids = [u.id for u in items]

    # Batch: emails
    auth_query = select(AuthUser.id, AuthUser.email).where(
        AuthUser.id.in_(user_ids),
    )
    auth_result = await db.execute(auth_query)
    emails = {row.id: row.email for row in auth_result.all()}

    # Batch: roles (via asignaciones activas, joined with Rol)
    asign_query = (
        select(Asignacion.usuario_id, Rol.nombre)
        .join(Rol, Asignacion.rol_id == Rol.id)
        .where(
            Asignacion.usuario_id.in_(user_ids),
            Asignacion.deleted_at.is_(None),
        )
        .distinct()
    )
    asign_result = await db.execute(asign_query)
    roles_map: dict[uuid.UUID, set[str]] = {}
    for row in asign_result.all():
        roles_map.setdefault(row.usuario_id, set()).add(row.nombre)

    # Filter by rol
    if rol:
        items = [u for u in items if rol in roles_map.get(u.id, set())]

    response_items = []
    for u in items:
        dto = UsuarioSafeResponse.model_validate(u)
        dto.email = emails.get(u.id)
        dto.roles = sorted(roles_map.get(u.id, set()))
        dto.activo = u.estado == "Activo"
        response_items.append(dto)

    return ListResponse(
        items=response_items,
        total=len(items),
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=UsuarioResponse, status_code=201)
async def create_usuario(
    body: UsuarioCreate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    roles = body.roles
    # Strip roles from body before passing to service (Usuario model has no roles field)
    create_data = body.model_dump(exclude={"roles"})
    repo = UsuarioRepository(db, current_user.tenant_id)
    service = UsuarioService(repo, db)
    entity = await service.create(create_data)
    pii_entity = await service.get_with_pii(entity.id)
    if pii_entity is None:
        raise HTTPException(status_code=500, detail="Failed to create usuario")

    # Create Asignacion records for each role
    if roles:
        from datetime import date
        for rol_nombre in roles:
            rol = (await db.execute(
                select(Rol).where(Rol.nombre == rol_nombre, Rol.tenant_id == current_user.tenant_id)
            )).scalar_one_or_none()
            if rol:
                db.add(Asignacion(
                    usuario_id=entity.id,
                    rol_id=rol.id,
                    tenant_id=current_user.tenant_id,
                    vig_desde=date.today(),
                ))
        await db.commit()

    return pii_entity


@router.get("/{id}", response_model=UsuarioResponse)
async def get_usuario(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = UsuarioRepository(db, current_user.tenant_id)
    service = UsuarioService(repo, db)
    entity = await service.get_with_pii(id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return entity


@router.put("/{id}", response_model=UsuarioResponse)
async def update_usuario(
    id: uuid.UUID,
    body: UsuarioUpdate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = UsuarioRepository(db, current_user.tenant_id)
    service = UsuarioService(repo, db)

    # Extract fields that don't belong to Usuario model
    roles = body.roles
    email = body.email
    password = body.password
    update_data = body.model_dump(exclude={"roles", "email", "password"}, exclude_none=True)

    # Update email on AuthUser if provided
    if email:
        auth_query = select(AuthUser).where(AuthUser.id == id)
        auth_result = await db.execute(auth_query)
        auth_user = auth_result.scalar_one_or_none()
        if auth_user:
            auth_user.email = email
            await db.commit()

    # Update password on AuthUser if provided
    if password:
        auth_query = select(AuthUser).where(AuthUser.id == id)
        auth_result = await db.execute(auth_query)
        auth_user = auth_result.scalar_one_or_none()
        if auth_user:
            auth_user.password_hash = hash_password(password)
            await db.commit()

    if not update_data and roles is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    entity = None
    if update_data:
        entity = await service.update(id, update_data)
        if entity is None:
            raise HTTPException(status_code=404, detail="Usuario not found")

    # Update roles: soft-delete existing, create new ones
    if roles is not None:
        from datetime import date
        existing = (await db.execute(
            select(Asignacion).where(
                Asignacion.usuario_id == id,
                Asignacion.deleted_at.is_(None),
            )
        )).scalars().all()
        for a in existing:
            a.deleted_at = func.now()
        for rol_nombre in roles:
            rol = (await db.execute(
                select(Rol).where(Rol.nombre == rol_nombre, Rol.tenant_id == current_user.tenant_id)
            )).scalar_one_or_none()
            if rol:
                db.add(Asignacion(
                    usuario_id=id,
                    rol_id=rol.id,
                    tenant_id=current_user.tenant_id,
                    vig_desde=date.today(),
                ))
        await db.commit()

    if entity is None:
        entity = await service.get_with_pii(id)
    return entity


@router.delete("/{id}", status_code=204)
async def delete_usuario(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = UsuarioRepository(db, current_user.tenant_id)
    service = UsuarioService(repo, db)
    deleted = await service.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario not found")


@router.patch("/{id}/estado", response_model=UsuarioSafeResponse)
async def toggle_usuario_estado(
    id: uuid.UUID,
    body: EstadoToggleRequest | None = None,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = UsuarioRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Usuario not found")
    if body and body.estado:
        entity.estado = body.estado
    else:
        entity.estado = "Inactivo" if entity.estado == "Activo" else "Activo"
    await db.commit()
    await db.refresh(entity)
    return entity


@router.post("/{id}/reset-password")
async def admin_reset_password(
    id: uuid.UUID,
    body: AdminResetPasswordRequest,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = UsuarioRepository(db, current_user.tenant_id)
    usuario = await repo.get(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    auth_repo = AuthRepository(db, current_user.tenant_id)
    auth_user = await auth_repo.get(id)
    if not auth_user:
        raise HTTPException(status_code=404, detail="Auth user not found")
    auth_user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password reset successfully"}
