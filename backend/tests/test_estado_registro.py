import pytest

from app.core.estado_registro import EstadoRegistro


class TestEstadoRegistro:
    def test_enum_members(self):
        assert EstadoRegistro.ACTIVA.value == "Activa"
        assert EstadoRegistro.INACTIVA.value == "Inactiva"

    def test_enum_iteration(self):
        members = list(EstadoRegistro)
        assert len(members) == 2
        assert EstadoRegistro.ACTIVA in members
        assert EstadoRegistro.INACTIVA in members

    def test_enum_from_value(self):
        assert EstadoRegistro("Activa") == EstadoRegistro.ACTIVA
        assert EstadoRegistro("Inactiva") == EstadoRegistro.INACTIVA

    def test_enum_from_name(self):
        assert EstadoRegistro["ACTIVA"] == EstadoRegistro.ACTIVA
        assert EstadoRegistro["INACTIVA"] == EstadoRegistro.INACTIVA

    def test_enum_invalid_value_raises(self):
        with pytest.raises(ValueError):
            EstadoRegistro("Unknown")
