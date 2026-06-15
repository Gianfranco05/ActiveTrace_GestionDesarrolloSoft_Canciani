import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.audit_codes import AuditAction
from app.models.aviso import Aviso
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.schemas.avisos import (
    AckResponse,
    AckStatsResponse,
    AlcanceEnum,
    AvisoCreateRequest,
    AvisoUpdateRequest,
    SeveridadEnum,
)
from app.services.aviso_service import AvisoService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_audit_service():
    svc = AsyncMock()
    svc.log = AsyncMock()
    return svc


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def actor_id():
    return uuid.uuid4()


@pytest.fixture
def usuario_id():
    return uuid.uuid4()


@pytest.fixture
def aviso_id():
    return uuid.uuid4()


@pytest.fixture
def sample_aviso(tenant_id, aviso_id):
    aviso = MagicMock(spec=Aviso)
    aviso.id = aviso_id
    aviso.tenant_id = tenant_id
    aviso.alcance = "Global"
    aviso.materia_id = None
    aviso.cohorte_id = None
    aviso.rol_destino = None
    aviso.severidad = "Info"
    aviso.titulo = "Test"
    aviso.cuerpo = "Cuerpo"
    aviso.inicio_en = datetime(2026, 1, 1, tzinfo=timezone.utc)
    aviso.fin_en = datetime(2030, 1, 1, tzinfo=timezone.utc)
    aviso.orden = 0
    aviso.activo = True
    aviso.requiere_ack = False
    aviso.created_at = datetime.now(timezone.utc)
    aviso.updated_at = datetime.now(timezone.utc)
    aviso.deleted_at = None
    return aviso


class TestAvisoServiceCreate:
    @pytest.mark.asyncio
    async def test_create_global_success(self, mock_session, mock_audit_service, tenant_id, actor_id, sample_aviso):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.create = AsyncMock(return_value=sample_aviso)

        data = AvisoCreateRequest(
            alcance=AlcanceEnum.Global,
            severidad=SeveridadEnum.Info,
            titulo="Test",
            cuerpo="Cuerpo",
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        result = await service.create(data, actor_id)

        assert result.id == sample_aviso.id
        mock_audit_service.log.assert_called_once_with(
            accion=AuditAction.AVISO_PUBLICAR,
            actor_id=actor_id,
            tenant_id=tenant_id,
            filas_afectadas=1,
        )

    @pytest.mark.asyncio
    async def test_create_inicio_after_fin_raises(self, mock_session, mock_audit_service, tenant_id, actor_id):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)

        data = AvisoCreateRequest(
            alcance=AlcanceEnum.Global,
            severidad=SeveridadEnum.Info,
            titulo="Test",
            cuerpo="Cuerpo",
            inicio_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await service.create(data, actor_id)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_create_por_materia_without_materia_id(self, mock_session, mock_audit_service, tenant_id, actor_id):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)

        data = AvisoCreateRequest(
            alcance=AlcanceEnum.PorMateria,
            severidad=SeveridadEnum.Info,
            titulo="Test",
            cuerpo="Cuerpo",
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await service.create(data, actor_id)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_create_por_cohorte_without_cohorte_id(self, mock_session, mock_audit_service, tenant_id, actor_id):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)

        data = AvisoCreateRequest(
            alcance=AlcanceEnum.PorCohorte,
            severidad=SeveridadEnum.Info,
            titulo="Test",
            cuerpo="Cuerpo",
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await service.create(data, actor_id)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_create_por_rol_without_rol_destino(self, mock_session, mock_audit_service, tenant_id, actor_id):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)

        data = AvisoCreateRequest(
            alcance=AlcanceEnum.PorRol,
            severidad=SeveridadEnum.Info,
            titulo="Test",
            cuerpo="Cuerpo",
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await service.create(data, actor_id)
        assert exc.value.status_code == 422


class TestAvisoServiceAcknowledge:
    @pytest.mark.asyncio
    async def test_acknowledge_creates_new_returns_201(
        self, mock_session, mock_audit_service, tenant_id, actor_id, usuario_id, aviso_id, sample_aviso,
    ):
        sample_aviso.requiere_ack = True
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=sample_aviso)
        service._repo.is_visible_by_scope = AsyncMock(return_value=True)

        ack_result = MagicMock(spec=AcknowledgmentAviso)
        ack_result.aviso_id = aviso_id
        ack_result.usuario_id = usuario_id
        ack_result.confirmado_at = datetime.now(timezone.utc)
        service._repo.create_ack = AsyncMock(return_value=ack_result)

        response, status_code = await service.acknowledge(aviso_id, usuario_id, actor_id)

        assert status_code == 201
        assert response.aviso_id == aviso_id
        assert response.usuario_id == usuario_id
        mock_audit_service.log.assert_called_once_with(
            accion=AuditAction.AVISO_CONFIRMAR,
            actor_id=actor_id,
            tenant_id=tenant_id,
            filas_afectadas=1,
        )

    @pytest.mark.asyncio
    async def test_acknowledge_idempotent_returns_200(
        self, mock_session, mock_audit_service, tenant_id, actor_id, usuario_id, aviso_id, sample_aviso,
    ):
        sample_aviso.requiere_ack = True
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=sample_aviso)
        service._repo.is_visible_by_scope = AsyncMock(return_value=True)
        service._repo.create_ack = AsyncMock(return_value=None)

        existing_ack = MagicMock(spec=AcknowledgmentAviso)
        existing_ack.aviso_id = aviso_id
        existing_ack.usuario_id = usuario_id
        existing_ack.confirmado_at = datetime.now(timezone.utc)
        service._repo.get_ack = AsyncMock(return_value=existing_ack)

        response, status_code = await service.acknowledge(aviso_id, usuario_id, actor_id)

        assert status_code == 200
        assert response.aviso_id == aviso_id
        mock_audit_service.log.assert_not_called()

    @pytest.mark.asyncio
    async def test_acknowledge_sin_requiere_ack_raises_422(
        self, mock_session, mock_audit_service, tenant_id, actor_id, usuario_id, aviso_id, sample_aviso,
    ):
        sample_aviso.requiere_ack = False
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=sample_aviso)

        with pytest.raises(HTTPException) as exc:
            await service.acknowledge(aviso_id, usuario_id, actor_id)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_acknowledge_aviso_not_found_404(
        self, mock_session, mock_audit_service, tenant_id, actor_id, usuario_id, aviso_id,
    ):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.acknowledge(aviso_id, usuario_id, actor_id)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_fuera_vigencia_404(
        self, mock_session, mock_audit_service, tenant_id, actor_id, usuario_id, aviso_id, sample_aviso,
    ):
        sample_aviso.requiere_ack = True
        sample_aviso.inicio_en = datetime(2030, 1, 1, tzinfo=timezone.utc)
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=sample_aviso)

        with pytest.raises(HTTPException) as exc:
            await service.acknowledge(aviso_id, usuario_id, actor_id)
        assert exc.value.status_code == 404


class TestAvisoServiceStats:
    @pytest.mark.asyncio
    async def test_get_stats_calculates_correctly(
        self, mock_session, mock_audit_service, tenant_id, aviso_id, sample_aviso,
    ):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=sample_aviso)
        service._repo.count_distinct_users = AsyncMock(return_value=10)
        service._repo.count_acks = AsyncMock(return_value=7)

        result = await service.get_stats(aviso_id)

        assert result.aviso_id == aviso_id
        assert result.total_views == 10
        assert result.total_acks == 7
        assert result.pendientes_ack == 3

    @pytest.mark.asyncio
    async def test_get_stats_no_views(
        self, mock_session, mock_audit_service, tenant_id, aviso_id, sample_aviso,
    ):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=sample_aviso)
        service._repo.count_distinct_users = AsyncMock(return_value=0)
        service._repo.count_acks = AsyncMock(return_value=0)

        result = await service.get_stats(aviso_id)

        assert result.total_views == 0
        assert result.total_acks == 0
        assert result.pendientes_ack == 0

    @pytest.mark.asyncio
    async def test_get_stats_aviso_not_found(
        self, mock_session, mock_audit_service, tenant_id, aviso_id,
    ):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_aviso_detail = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.get_stats(aviso_id)
        assert exc.value.status_code == 404


class TestAvisoServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_session, mock_audit_service, tenant_id, actor_id, aviso_id):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_by_id = AsyncMock(return_value=None)

        data = AvisoUpdateRequest(titulo="Nuevo")
        with pytest.raises(HTTPException) as exc:
            await service.update(aviso_id, data, actor_id)
        assert exc.value.status_code == 404


class TestAvisoServiceSoftDelete:
    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self, mock_session, mock_audit_service, tenant_id, actor_id, aviso_id):
        service = AvisoService(mock_session, mock_audit_service, tenant_id)
        service._repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.soft_delete(aviso_id, actor_id)
        assert exc.value.status_code == 404
