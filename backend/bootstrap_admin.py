"""Crea el usuario ADMIN por defecto si no existe — idempotente.

Uso manual:
    python bootstrap_admin.py

Uso Docker:
    Se ejecuta como servicio "seeder" en docker-compose después de las migraciones.
    Lee DATABASE_URL, SECRET_KEY, ENCRYPTION_KEY del entorno (sin hardcodear nada).

Credenciales por defecto:
    admin@activia.com / Admin123!
"""

import asyncio
import os
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

# ── Config desde entorno (docker-compose las inyecta) ──────────────────
try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as exc:
    print(f"❌ Error al cargar configuración: {exc}")
    print("   Asegurate de que backend/.env tenga SECRET_KEY y ENCRYPTION_KEY válidas.")
    print("   SECRET_KEY: al menos 32 caracteres.")
    print("   ENCRYPTION_KEY: exactamente 32 caracteres.")
    sys.exit(1)

engine = create_engine(settings)
factory = create_session_factory(engine)


async def bootstrap() -> None:
    async with factory() as session:
        # 1. Obtener tenant "default"
        result = await session.execute(
            select(Tenant).where(Tenant.slug == "default")
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            print("❌ No se encontró el tenant 'default'. ¿Corriste las migraciones?")
            sys.exit(1)
        print(f"✅ Tenant: {tenant.name} ({tenant.id})")

        # 2. Obtener rol ADMIN
        result = await session.execute(
            select(Rol).where(
                Rol.nombre == "ADMIN",
                Rol.tenant_id == tenant.id,
            )
        )
        rol = result.scalar_one_or_none()
        if rol is None:
            print("❌ No se encontró el rol ADMIN. ¿Corriste las migraciones?")
            sys.exit(1)
        print(f"✅ Rol ADMIN: {rol.id}")

        # 3. Verificar si ya existe el admin (IDEMPOTENTE)
        result = await session.execute(
            select(AuthUser).where(
                AuthUser.tenant_id == tenant.id,
                AuthUser.email == "admin@activia.com",
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"ℹ️  Admin ya existe: {existing.email} (id={existing.id})")
            print("   Credenciales: admin@activia.com / Admin123!")
            return

        # 4. Crear AuthUser + Usuario + Asignacion
        user_id = uuid.uuid4()

        auth = AuthUser(
            id=user_id,
            tenant_id=tenant.id,
            email="admin@activia.com",
            password_hash=hash_password("Admin123!"),
            is_active=True,
        )

        usuario = Usuario(
            id=user_id,
            tenant_id=tenant.id,
            nombre="Admin",
            apellidos="Sistema",
            dni="00000000",
            cuil="00000000000",
        )

        asignacion = Asignacion(
            usuario_id=user_id,
            rol_id=rol.id,
            tenant_id=tenant.id,
            vig_desde=date.today(),
        )

        session.add_all([auth, usuario, asignacion])
        await session.commit()
        print("✅ Admin creado: admin@activia.com / Admin123!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(bootstrap())
