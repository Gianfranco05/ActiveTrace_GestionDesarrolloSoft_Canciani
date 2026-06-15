"""TDD: Liquidacion models — SalarioBase, SalarioPlus, GrupoMateria, Liquidacion, Factura."""

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.carrera import Carrera
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.liquidacion import (
    SalarioBase,
    SalarioPlus,
    GrupoMateria,
    Liquidacion,
    Factura,
)


@pytest.fixture
async def auth_and_user(db_session, tenant):
    auth = AuthUser(
        id=uuid.uuid4(),
        email="test_liquidacion@test.com",
        password_hash="test_hash",
        tenant_id=tenant.id,
    )
    db_session.add(auth)
    await db_session.flush()
    user = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Juan",
        apellidos="Perez",
        legajo="LQ001",
    )
    db_session.add(user)
    await db_session.commit()
    return auth, user


@pytest.fixture
async def carrera_fixture(db_session, tenant):
    c = Carrera(
        tenant_id=tenant.id,
        codigo=f"CARR-{uuid.uuid4().hex[:8]}",
        nombre="Ingenieria en Sistemas",
        estado="Activa",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


@pytest.fixture
async def materia_fixture(db_session, tenant):
    m = Materia(
        tenant_id=tenant.id,
        codigo=f"MAT-{uuid.uuid4().hex[:8]}",
        nombre="Matematica Discreta",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


@pytest.fixture
async def cohorte_fixture(db_session, tenant, carrera_fixture):
    co = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera_fixture.id,
        nombre="Cohorte 2025",
        anio=2025,
        vig_desde=date(2025, 1, 1),
        estado="Activa",
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)
    return co


class TestSalarioBaseModel:
    async def test_salario_base_creation(self, db_session, tenant):
        entity = SalarioBase(
            tenant_id=tenant.id,
            rol="PROFESOR",
            monto=50000.00,
            vig_desde=date(2025, 1, 1),
        )
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        assert entity.id is not None
        assert entity.rol == "PROFESOR"
        assert entity.monto == 50000.00
        assert entity.vig_desde == date(2025, 1, 1)
        assert entity.vig_hasta is None
        assert entity.created_at is not None
        assert entity.deleted_at is None

    async def test_salario_base_with_vig_hasta(self, db_session, tenant):
        entity = SalarioBase(
            tenant_id=tenant.id,
            rol="TUTOR",
            monto=40000.00,
            vig_desde=date(2025, 1, 1),
            vig_hasta=date(2025, 12, 31),
        )
        db_session.add(entity)
        await db_session.commit()
        assert entity.vig_hasta == date(2025, 12, 31)

    async def test_salario_base_soft_delete(self, db_session, tenant):
        entity = SalarioBase(
            tenant_id=tenant.id,
            rol="COORDINADOR",
            monto=60000.00,
            vig_desde=date(2025, 1, 1),
        )
        db_session.add(entity)
        await db_session.commit()
        entity.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        assert entity.deleted_at is not None
        result = await db_session.execute(
            select(SalarioBase).where(
                SalarioBase.id == entity.id,
                SalarioBase.deleted_at.is_(None),
            )
        )
        assert result.scalar_one_or_none() is None


class TestSalarioPlusModel:
    async def test_salario_plus_creation(self, db_session, tenant):
        entity = SalarioPlus(
            tenant_id=tenant.id,
            grupo="PROG",
            rol="PROFESOR",
            descripcion="Plus por programacion",
            monto=5000.00,
            vig_desde=date(2025, 1, 1),
        )
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        assert entity.id is not None
        assert entity.grupo == "PROG"
        assert entity.rol == "PROFESOR"
        assert entity.monto == 5000.00

    async def test_salario_plus_soft_delete(self, db_session, tenant):
        entity = SalarioPlus(
            tenant_id=tenant.id,
            grupo="BD",
            rol="TUTOR",
            descripcion="Plus por base de datos",
            monto=3000.00,
            vig_desde=date(2025, 1, 1),
        )
        db_session.add(entity)
        await db_session.commit()
        entity.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        result = await db_session.execute(
            select(SalarioPlus).where(
                SalarioPlus.id == entity.id,
                SalarioPlus.deleted_at.is_(None),
            )
        )
        assert result.scalar_one_or_none() is None


class TestGrupoMateriaModel:
    async def test_grupo_materia_creation(self, db_session, tenant, materia_fixture):
        entity = GrupoMateria(
            tenant_id=tenant.id,
            grupo="PROG",
            materia_id=materia_fixture.id,
        )
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        assert entity.id is not None
        assert entity.grupo == "PROG"
        assert entity.materia_id == materia_fixture.id

    async def test_grupo_materia_soft_delete(self, db_session, tenant, materia_fixture):
        entity = GrupoMateria(
            tenant_id=tenant.id,
            grupo="BD",
            materia_id=materia_fixture.id,
        )
        db_session.add(entity)
        await db_session.commit()
        entity.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        result = await db_session.execute(
            select(GrupoMateria).where(
                GrupoMateria.id == entity.id,
                GrupoMateria.deleted_at.is_(None),
            )
        )
        assert result.scalar_one_or_none() is None


class TestLiquidacionModel:
    async def test_liquidacion_creation(
        self, db_session, tenant, auth_and_user, cohorte_fixture
    ):
        _, user = auth_and_user
        entity = Liquidacion(
            tenant_id=tenant.id,
            cohorte_id=cohorte_fixture.id,
            periodo="2025-06",
            usuario_id=user.id,
            rol="PROFESOR",
            comisiones="M1, M2",
            monto_base=50000.00,
            monto_plus=10000.00,
            total=60000.00,
            es_nexo=False,
            excluido_por_factura=False,
            estado="Abierta",
        )
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        assert entity.id is not None
        assert entity.periodo == "2025-06"
        assert entity.estado == "Abierta"
        assert entity.monto_base == 50000.00
        assert entity.monto_plus == 10000.00
        assert entity.total == 60000.00

    async def test_liquidacion_defaults(
        self, db_session, tenant, auth_and_user, cohorte_fixture
    ):
        _, user = auth_and_user
        entity = Liquidacion(
            tenant_id=tenant.id,
            cohorte_id=cohorte_fixture.id,
            periodo="2025-06",
            usuario_id=user.id,
            rol="PROFESOR",
            monto_base=50000.00,
            monto_plus=0,
            total=50000.00,
        )
        db_session.add(entity)
        await db_session.commit()
        assert entity.es_nexo is False
        assert entity.excluido_por_factura is False
        assert entity.monto_plus == 0

    async def test_liquidacion_nexo_flag(
        self, db_session, tenant, auth_and_user, cohorte_fixture
    ):
        _, user = auth_and_user
        entity = Liquidacion(
            tenant_id=tenant.id,
            cohorte_id=cohorte_fixture.id,
            periodo="2025-06",
            usuario_id=user.id,
            rol="NEXO",
            monto_base=30000.00,
            monto_plus=0,
            total=30000.00,
            es_nexo=True,
        )
        db_session.add(entity)
        await db_session.commit()
        assert entity.es_nexo is True

    async def test_liquidacion_facturante_flag(
        self, db_session, tenant, auth_and_user, cohorte_fixture
    ):
        _, user = auth_and_user
        entity = Liquidacion(
            tenant_id=tenant.id,
            cohorte_id=cohorte_fixture.id,
            periodo="2025-06",
            usuario_id=user.id,
            rol="PROFESOR",
            monto_base=0,
            monto_plus=0,
            total=0,
            excluido_por_factura=True,
        )
        db_session.add(entity)
        await db_session.commit()
        assert entity.excluido_por_factura is True


class TestFacturaModel:
    async def test_factura_creation(self, db_session, tenant, auth_and_user):
        _, user = auth_and_user
        entity = Factura(
            tenant_id=tenant.id,
            usuario_id=user.id,
            periodo="2025-06",
            detalle="Factura de honorarios junio 2025",
            referencia_archivo="facturas/2025-06/juan.pdf",
            tamano_kb=150.5,
            estado="Pendiente",
        )
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        assert entity.id is not None
        assert entity.estado == "Pendiente"
        assert entity.cargada_at is not None
        assert entity.abonada_at is None
        assert entity.cohorte_id is None
        assert entity.tamano_kb == 150.5

    async def test_factura_with_cohorte(
        self, db_session, tenant, auth_and_user, cohorte_fixture
    ):
        _, user = auth_and_user
        entity = Factura(
            tenant_id=tenant.id,
            usuario_id=user.id,
            cohorte_id=cohorte_fixture.id,
            periodo="2025-06",
            detalle="Factura con cohorte",
        )
        db_session.add(entity)
        await db_session.commit()
        assert entity.cohorte_id is not None
        assert entity.referencia_archivo is None

    async def test_factura_defaults(self, db_session, tenant, auth_and_user):
        _, user = auth_and_user
        entity = Factura(
            tenant_id=tenant.id,
            usuario_id=user.id,
            periodo="2025-06",
            detalle="Factura por defecto",
        )
        db_session.add(entity)
        await db_session.commit()
        assert entity.estado == "Pendiente"
        assert entity.cargada_at is not None

    async def test_factura_soft_delete(self, db_session, tenant, auth_and_user):
        _, user = auth_and_user
        entity = Factura(
            tenant_id=tenant.id,
            usuario_id=user.id,
            periodo="2025-06",
            detalle="A borrar",
        )
        db_session.add(entity)
        await db_session.commit()
        entity.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        result = await db_session.execute(
            select(Factura).where(
                Factura.id == entity.id,
                Factura.deleted_at.is_(None),
            )
        )
        assert result.scalar_one_or_none() is None
