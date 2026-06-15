"""TDD: Factura Service — CRUD and state machine tests."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.liquidacion import Factura
from app.services.factura_service import FacturaService
from app.schemas.liquidacion import FacturaCreate, FacturaUpdate


@pytest_asyncio.fixture
async def facturador_user(db_session: AsyncSession, tenant):
    auth = AuthUser(
        id=uuid.uuid4(),
        email="facturador@test.com",
        password_hash="test_hash",
        tenant_id=tenant.id,
    )
    db_session.add(auth)
    await db_session.flush()
    user = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Factura",
        apellidos="Dora",
        legajo="FC001",
        facturador=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def no_facturador_user(db_session: AsyncSession, tenant):
    auth = AuthUser(
        id=uuid.uuid4(),
        email="no_facturador@test.com",
        password_hash="test_hash",
        tenant_id=tenant.id,
    )
    db_session.add(auth)
    await db_session.flush()
    user = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="No",
        apellidos="Facturador",
        legajo="NF001",
        facturador=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


def _svc(db_session, tenant) -> FacturaService:
    return FacturaService(db_session, tenant.id)


class TestFacturaCreate:
    async def test_create_factura_success(self, db_session, tenant, facturador_user):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="Factura de honorarios junio",
            referencia_archivo="facturas/2025-06/fact.pdf",
            tamano_kb=Decimal("150.5"),
        )
        factura = await svc.create(data)
        assert factura.id is not None
        assert factura.estado == "Pendiente"
        assert factura.detalle == "Factura de honorarios junio"
        assert factura.usuario_id == facturador_user.id
        assert factura.cargada_at is not None
        assert factura.abonada_at is None

    async def test_create_factura_no_facturador_rejected(
        self, db_session, tenant, no_facturador_user
    ):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=no_facturador_user.id,
            periodo="2025-06",
            detalle="No deberia crearse",
        )
        with pytest.raises(HTTPException) as exc:
            await svc.create(data)
        assert exc.value.status_code == 409
        assert "facturador" in exc.value.detail.lower()


class TestFacturaRead:
    async def test_get_by_id(self, db_session, tenant, facturador_user):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="Factura a buscar",
        )
        created = await svc.create(data)
        found = await svc.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    async def test_get_by_id_tenant_isolation(self, db_session, tenant, facturador_user):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="Tenant isolation",
        )
        created = await svc.create(data)
        other_svc = FacturaService(db_session, uuid.uuid4())
        found = await other_svc.get_by_id(created.id)
        assert found is None

    async def test_list_all_empty(self, db_session, tenant):
        svc = _svc(db_session, tenant)
        items = await svc.list_all()
        assert items == []

    async def test_list_all_with_filters(self, db_session, tenant, facturador_user):
        svc = _svc(db_session, tenant)
        data1 = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="Factura 1",
        )
        data2 = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-07",
            detalle="Factura 2",
        )
        await svc.create(data1)
        await svc.create(data2)

        all_items = await svc.list_all()
        assert len(all_items) == 2

        filtered = await svc.list_all(periodo="2025-06")
        assert len(filtered) == 1
        assert filtered[0].periodo == "2025-06"


class TestFacturaSoftDelete:
    async def test_soft_delete(self, db_session, tenant, facturador_user):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="A eliminar",
        )
        created = await svc.create(data)
        result = await svc.soft_delete(created.id)
        assert result is True

        found = await svc.get_by_id(created.id)
        assert found is None

    async def test_soft_delete_not_found(self, db_session, tenant):
        svc = _svc(db_session, tenant)
        result = await svc.soft_delete(uuid.uuid4())
        assert result is False


class TestFacturaAbonar:
    async def test_abonar_pendiente_transitions_to_abonada(
        self, db_session, tenant, facturador_user
    ):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="A abonar",
        )
        created = await svc.create(data)
        assert created.estado == "Pendiente"
        assert created.abonada_at is None

        abonada = await svc.abonar(created.id)
        assert abonada.estado == "Abonada"
        assert abonada.abonada_at is not None

    async def test_abonar_already_abonada_returns_409(
        self, db_session, tenant, facturador_user
    ):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="Ya abonada",
        )
        created = await svc.create(data)
        await svc.abonar(created.id)

        with pytest.raises(HTTPException) as exc:
            await svc.abonar(created.id)
        assert exc.value.status_code == 409

    async def test_abonar_not_found_returns_404(
        self, db_session, tenant
    ):
        svc = _svc(db_session, tenant)
        with pytest.raises(HTTPException) as exc:
            await svc.abonar(uuid.uuid4())
        assert exc.value.status_code == 404


class TestFacturaReabrir:
    async def test_reabrir_abonada_transitions_to_pendiente(
        self, db_session, tenant, facturador_user
    ):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="A reabrir",
        )
        created = await svc.create(data)
        await svc.abonar(created.id)

        reopened = await svc.reabrir(created.id)
        assert reopened.estado == "Pendiente"
        assert reopened.abonada_at is None

    async def test_reabrir_pendiente_returns_409(
        self, db_session, tenant, facturador_user
    ):
        svc = _svc(db_session, tenant)
        data = FacturaCreate(
            usuario_id=facturador_user.id,
            periodo="2025-06",
            detalle="Ya pendiente",
        )
        created = await svc.create(data)

        with pytest.raises(HTTPException) as exc:
            await svc.reabrir(created.id)
        assert exc.value.status_code == 409

    async def test_reabrir_not_found_returns_404(
        self, db_session, tenant
    ):
        svc = _svc(db_session, tenant)
        with pytest.raises(HTTPException) as exc:
            await svc.reabrir(uuid.uuid4())
        assert exc.value.status_code == 404
