import pytest
from app.services.usuario_service import UsuarioService


@pytest.mark.asyncio
async def test_create_usuario_service_creates_and_links(db_session, tenant):
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Svc", "apellidos": "Test", "dni": "999"}
    u = await service.create(data)
    assert u.id is not None
    assert str(u.tenant_id) == str(tenant.id)


@pytest.mark.asyncio
async def test_create_usuario_service_rejects_duplicate_dni(db_session, tenant):
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Svc1", "apellidos": "A", "dni": "111"}
    u1 = await service.create(data)
    # try to create another with same dni in same tenant -> expect error
    data2 = {"nombre": "Svc2", "apellidos": "B", "dni": "111"}
    with pytest.raises(Exception):
        await service.create(data2)
