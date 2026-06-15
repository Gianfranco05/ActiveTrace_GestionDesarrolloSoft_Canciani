import pytest
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioSafeResponse


def test_usuario_create_extra_fields_rejected():
    data = {"nombre": "A", "apellidos": "B", "unknown": 1}
    with pytest.raises(Exception):
        UsuarioCreate(**data)


def test_usuario_response_from_model():
    class Dummy:
        id = "uuid"
        tenant_id = "t"
        nombre = "A"
        apellidos = "B"
        dni = "x"
        cuil = "y"
        cbu = "z"
        alias_cbu = "a"
        facturador = False
        estado = "Activo"

    u = Dummy()
    resp = UsuarioResponse.from_orm(u)
    assert resp.id == "uuid"
    safe = UsuarioSafeResponse.from_orm(u)
    assert not hasattr(safe, "dni")
