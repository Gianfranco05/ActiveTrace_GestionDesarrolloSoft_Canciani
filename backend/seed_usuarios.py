"""Siembra usuarios demo: uno por cada rol + 5 alumnos.
Uso: python seed_usuarios.py
"""
import asyncio
import sys
import uuid
from datetime import date

from sqlalchemy import select

from app.core.config import Settings
from app.core.database import create_engine, create_session_factory
from app.core.security import hash_password
from app.models.asignacion import Asignacion
from app.models.auth_user import AuthUser
from app.models.rol import Rol
from app.models.tenant import Tenant
from app.models.usuario import Usuario

try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as exc:
    print(f"Error al cargar config: {exc}")
    sys.exit(1)

engine = create_engine(settings)
factory = create_session_factory(engine)

USUARIOS = [
    # (nombre, apellidos, email, rol_nombre)
    ("Alumno 1", "Demo", "alumno1@gmail.com", "ALUMNO"),
    ("Alumno 2", "Demo", "alumno2@gmail.com", "ALUMNO"),
    ("Alumno 3", "Demo", "alumno3@gmail.com", "ALUMNO"),
    ("Alumno 4", "Demo", "alumno4@gmail.com", "ALUMNO"),
    ("Alumno 5", "Demo", "alumno5@gmail.com", "ALUMNO"),
    ("Tutor", "Demo", "tutor@gmail.com", "TUTOR"),
    ("Profesor", "Demo", "profesor@gmail.com", "PROFESOR"),
    ("Coordinador", "Demo", "coordinador@gmail.com", "COORDINADOR"),
    ("Nexo", "Demo", "nexo@gmail.com", "NEXO"),
    ("Finanzas", "Demo", "finanzas@gmail.com", "FINANZAS"),
]


async def seed() -> None:
    async with factory() as session:
        # Obtener tenant default
        result = await session.execute(
            select(Tenant).where(Tenant.slug == "default")
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            print("No se encontró el tenant 'default'.")
            sys.exit(1)
        print(f"Tenant: {tenant.name} ({tenant.id})")

        # Cargar roles
        result = await session.execute(
            select(Rol).where(Rol.tenant_id == tenant.id)
        )
        roles = {r.nombre: r for r in result.scalars().all()}
        print(f"Roles disponibles: {list(roles.keys())}")

        creados = 0
        for nombre, apellidos, email, rol_nombre in USUARIOS:
            # Verificar si ya existe
            result = await session.execute(
                select(AuthUser).where(
                    AuthUser.tenant_id == tenant.id,
                    AuthUser.email == email,
                )
            )
            if result.scalar_one_or_none():
                print(f"  [SKIP] {email} ya existe")
                continue

            rol = roles.get(rol_nombre)
            if rol is None:
                print(f"  [ERROR] Rol '{rol_nombre}' no encontrado para {email}")
                continue

            user_id = uuid.uuid4()

            auth = AuthUser(
                id=user_id,
                tenant_id=tenant.id,
                email=email,
                password_hash=hash_password("123456"),
                is_active=True,
            )

            usuario = Usuario(
                id=user_id,
                tenant_id=tenant.id,
                nombre=nombre,
                apellidos=apellidos,
            )

            asignacion = Asignacion(
                usuario_id=user_id,
                rol_id=rol.id,
                tenant_id=tenant.id,
                vig_desde=date.today(),
            )

            session.add_all([auth, usuario, asignacion])
            creados += 1
            print(f"  [OK] {email} ({rol_nombre}) - creado")

        await session.commit()
        print(f"\n{creados} usuarios creados. Password: 123456")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
