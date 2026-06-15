"""TDD: Shared test helpers for encuentros y guardias."""

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion


async def create_asignacion_chain(
    db_session: AsyncSession, tenant, suid: str | None = None
):
    suid = suid or uuid.uuid4().hex[:6]
    materia = Materia(codigo=f"TH-{suid}", nombre="Materia Helper", tenant_id=tenant.id)
    db_session.add(materia)

    carrera = Carrera(codigo=f"THC-{suid}", nombre="Carrera Helper", tenant_id=tenant.id)
    db_session.add(carrera)

    au = AuthUser(
        tenant_id=tenant.id,
        email=f"helper_{suid}@t.com",
        password_hash="x",
    )
    db_session.add(au)
    await db_session.flush()

    usuario = Usuario(
        id=au.id, tenant_id=tenant.id, nombre="Helper", apellidos="Test",
        legajo=f"HLP-{suid}",
    )
    db_session.add(usuario)

    rol = Rol(nombre=f"HELPER-{suid}", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre=f"CH-{suid}", anio=2026,
        vig_desde=date(2026, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.flush()

    asignacion = Asignacion(
        usuario_id=usuario.id,
        rol_id=rol.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        tenant_id=tenant.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asignacion)
    await db_session.commit()
    await db_session.refresh(asignacion)

    return asignacion, materia, carrera, cohorte
