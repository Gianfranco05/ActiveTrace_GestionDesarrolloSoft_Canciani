import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.audit import AuditLogListResponse, AuditLogResponse


class TestAuditLogResponse:

    def test_serialization(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "fecha_hora": now,
            "actor_id": uuid.uuid4(),
            "accion": "CALIFICACIONES_IMPORTAR",
            "filas_afectadas": 5,
            "detalle": {"key": "value"},
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": now,
        }
        resp = AuditLogResponse(**data)
        assert resp.accion == "CALIFICACIONES_IMPORTAR"
        assert resp.filas_afectadas == 5
        assert resp.detalle == {"key": "value"}
        assert resp.ip == "192.168.1.1"

    def test_optional_fields_default_to_none(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "fecha_hora": now,
            "actor_id": uuid.uuid4(),
            "accion": "PADRON_CARGAR",
            "created_at": now,
        }
        resp = AuditLogResponse(**data)
        assert resp.impersonado_id is None
        assert resp.materia_id is None
        assert resp.detalle is None
        assert resp.ip is None
        assert resp.user_agent is None
        assert resp.filas_afectadas == 0

    def test_extra_fields_rejected(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "fecha_hora": now,
            "actor_id": uuid.uuid4(),
            "accion": "TEST",
            "created_at": now,
            "extra_field": "should_not_exist",
        }
        with pytest.raises(ValidationError):
            AuditLogResponse(**data)

    def test_audit_log_list_response(self):
        now = datetime.now(timezone.utc)
        item = {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "fecha_hora": now,
            "actor_id": uuid.uuid4(),
            "accion": "TEST",
            "created_at": now,
        }
        list_resp = AuditLogListResponse(
            items=[AuditLogResponse(**item)],
            total=1,
            offset=0,
            limit=50,
        )
        assert len(list_resp.items) == 1
        assert list_resp.total == 1
        assert list_resp.offset == 0
        assert list_resp.limit == 50
        assert list_resp.items[0].accion == "TEST"
