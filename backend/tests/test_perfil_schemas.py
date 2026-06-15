import pytest
from pydantic import ValidationError

from app.schemas.perfil import PerfilResponse, PerfilUpdateRequest


def test_perfil_update_rejects_cuil():
    with pytest.raises(ValidationError):
        PerfilUpdateRequest(cuil="20-12345678-9")


def test_perfil_update_rejects_extra_fields():
    with pytest.raises(ValidationError):
        PerfilUpdateRequest(extra_field="value")


def test_perfil_update_partial_fields():
    req = PerfilUpdateRequest(nombre="Carlos")
    assert req.nombre == "Carlos"
    assert req.apellidos is None
    assert req.dni is None


def test_perfil_response_includes_cuil():
    resp = PerfilResponse(
        id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000001",
        nombre="Test",
        apellidos="User",
        email="test@test.com",
        dni="12345678",
        cuil="20-12345678-9",
        banco=None,
        cbu=None,
        alias_cbu=None,
        regional=None,
        legajo=None,
        legajo_profesional=None,
        facturador=False,
        estado="Activo",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert resp.cuil == "20-12345678-9"


def test_perfil_update_nombre_max_length():
    req = PerfilUpdateRequest(nombre="a" * 120)
    assert len(req.nombre) == 120

    with pytest.raises(ValidationError):
        PerfilUpdateRequest(nombre="a" * 121)


def test_perfil_update_banco_max_length():
    req = PerfilUpdateRequest(banco="a" * 80)
    assert len(req.banco) == 80

    with pytest.raises(ValidationError):
        PerfilUpdateRequest(banco="a" * 81)
