
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
    await service.create(data)
    data2 = {"nombre": "Svc2", "apellidos": "B", "dni": "111"}
    with pytest.raises(Exception):
        await service.create(data2)


@pytest.mark.asyncio
async def test_get_with_pii_decrypts(db_session, tenant):
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Pii", "apellidos": "Test", "dni": "12345678", "cuil": "20-12345678-9", "cbu": "0123456789012345678901"}
    u = await service.create(data)
    pii = await service.get_with_pii(u.id)
    assert pii is not None
    assert pii["dni"] == "12345678"
    assert pii["cuil"] == "20-12345678-9"
    assert pii["cbu"] == "0123456789012345678901"


@pytest.mark.asyncio
async def test_get_safe_returns_no_pii(db_session, tenant):
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Safe", "apellidos": "Test", "dni": "87654321", "cuil": "20-87654321-0"}
    await service.create(data)
    items = await service.list()
    for item in items:
        raw = item.__dict__
        stored_dni = raw.get("dni")
        if stored_dni is not None:
            assert stored_dni != "87654321"
            from app.core.security import decrypt_or_none
            assert decrypt_or_none(stored_dni) == "87654321"


@pytest.mark.asyncio
async def test_update_encrypts_new_pii(db_session, tenant):
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Upd", "apellidos": "Test"}
    u = await service.create(data)
    updated = await service.update(u.id, {"dni": "99999999", "cuil": "20-99999999-9"})
    assert updated is not None
    raw_dni = updated.__dict__.get("dni")
    assert raw_dni != "99999999"
    from app.core.security import decrypt_or_none
    assert decrypt_or_none(raw_dni) == "99999999"


@pytest.mark.asyncio
async def test_create_pii_not_in_logs(db_session, tenant, caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Log", "apellidos": "Check", "dni": "55555555", "cuil": "20-55555555-5"}
    await service.create(data)
    assert "55555555" not in caplog.text
    assert "20-55555555-5" not in caplog.text


@pytest.mark.asyncio
async def test_soft_delete_usuario_service(db_session, tenant):
    service = UsuarioService(db_session, tenant.id)
    data = {"nombre": "SvcDel", "apellidos": "Test"}
    u = await service.create(data)
    result = await service.soft_delete(u.id)
    assert result is True
    pii = await service.get_with_pii(u.id)
    assert pii is None
