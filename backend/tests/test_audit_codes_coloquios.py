from app.core.audit_codes import AuditAction


def test_coloquio_crear_defined():
    assert hasattr(AuditAction, "COLOQUIO_CREAR")
    assert AuditAction.COLOQUIO_CREAR == "COLOQUIO_CREAR"


def test_coloquio_reservar_defined():
    assert hasattr(AuditAction, "COLOQUIO_RESERVAR")
    assert AuditAction.COLOQUIO_RESERVAR == "COLOQUIO_RESERVAR"


def test_coloquio_cancelar_defined():
    assert hasattr(AuditAction, "COLOQUIO_CANCELAR")
    assert AuditAction.COLOQUIO_CANCELAR == "COLOQUIO_CANCELAR"


def test_coloquio_resultado_defined():
    assert hasattr(AuditAction, "COLOQUIO_RESULTADO")
    assert AuditAction.COLOQUIO_RESULTADO == "COLOQUIO_RESULTADO"
