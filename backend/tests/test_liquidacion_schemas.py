"""TDD: Liquidacion schemas — Pydantic v2 DTOs."""

import uuid
from decimal import Decimal
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.liquidacion import (
    SalarioBaseCreate,
    SalarioBaseUpdate,
    SalarioBaseResponse,
    SalarioPlusCreate,
    SalarioPlusUpdate,
    SalarioPlusResponse,
    GrupoMateriaCreate,
    GrupoMateriaResponse,
    LiquidacionResponse,
    LiquidacionKPIs,
    LiquidacionListResponse,
    CalcularLiquidacionRequest,
    CerrarLiquidacionRequest,
    FacturaCreate,
    FacturaResponse,
    FacturaUpdate,
)


class TestSalarioBaseSchemas:
    def test_salario_base_create_valid(self):
        s = SalarioBaseCreate(
            rol="PROFESOR",
            monto=Decimal("50000.00"),
            vig_desde=date(2025, 1, 1),
        )
        assert s.rol == "PROFESOR"
        assert s.monto == Decimal("50000.00")

    def test_salario_base_create_invalid_monto_negative(self):
        with pytest.raises(ValidationError):
            SalarioBaseCreate(
                rol="PROFESOR",
                monto=Decimal("-100.00"),
                vig_desde=date(2025, 1, 1),
            )

    def test_salario_base_create_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            SalarioBaseCreate(
                rol="PROFESOR",
                monto=Decimal("50000.00"),
                vig_desde=date(2025, 1, 1),
                campo_extra="no permitido",
            )

    def test_salario_base_update_partial(self):
        s = SalarioBaseUpdate(monto=Decimal("60000.00"))
        assert s.monto == Decimal("60000.00")
        assert s.rol is None

    def test_salario_base_response_from_attributes(self):
        data = {
            "id": uuid.uuid4(),
            "rol": "PROFESOR",
            "monto": Decimal("50000.00"),
            "vig_desde": date(2025, 1, 1),
            "vig_hasta": None,
        }
        s = SalarioBaseResponse.model_validate(data)
        assert s.rol == "PROFESOR"


class TestSalarioPlusSchemas:
    def test_salario_plus_create_valid(self):
        s = SalarioPlusCreate(
            grupo="PROG",
            rol="PROFESOR",
            descripcion="Plus programacion",
            monto=Decimal("5000.00"),
            vig_desde=date(2025, 1, 1),
        )
        assert s.grupo == "PROG"

    def test_salario_plus_create_empty_descripcion(self):
        with pytest.raises(ValidationError):
            SalarioPlusCreate(
                grupo="PROG",
                rol="PROFESOR",
                descripcion="",
                monto=Decimal("5000.00"),
                vig_desde=date(2025, 1, 1),
            )


class TestGrupoMateriaSchemas:
    def test_grupo_materia_create_valid(self):
        mid = uuid.uuid4()
        s = GrupoMateriaCreate(grupo="PROG", materia_id=mid)
        assert s.materia_id == mid

    def test_grupo_materia_response(self):
        mid = uuid.uuid4()
        data = {"id": uuid.uuid4(), "grupo": "PROG", "materia_id": mid}
        s = GrupoMateriaResponse.model_validate(data)
        assert s.grupo == "PROG"


class TestLiquidacionSchemas:
    def test_liquidacion_response_from_attributes(self):
        data = {
            "id": uuid.uuid4(),
            "cohorte_id": uuid.uuid4(),
            "periodo": "2025-06",
            "usuario_id": uuid.uuid4(),
            "rol": "PROFESOR",
            "comisiones": "M1, M2",
            "monto_base": Decimal("50000.00"),
            "monto_plus": Decimal("10000.00"),
            "total": Decimal("60000.00"),
            "es_nexo": False,
            "excluido_por_factura": False,
            "estado": "Abierta",
        }
        s = LiquidacionResponse.model_validate(data)
        assert s.periodo == "2025-06"
        assert s.total == Decimal("60000.00")

    def test_liquidacion_kpis_validation(self):
        data = {
            "total_general": Decimal("100000.00"),
            "total_sin_factura": Decimal("80000.00"),
            "total_nexo": Decimal("20000.00"),
            "total_facturantes": 2,
            "total_docentes": 10,
        }
        kpis = LiquidacionKPIs.model_validate(data)
        assert kpis.total_docentes == 10

    def test_liquidacion_list_response(self):
        liq = LiquidacionResponse(
            id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            periodo="2025-06",
            usuario_id=uuid.uuid4(),
            rol="PROFESOR",
            monto_base=Decimal("50000.00"),
            monto_plus=Decimal("0"),
            total=Decimal("50000.00"),
            es_nexo=False,
            excluido_por_factura=False,
            estado="Abierta",
        )
        kpis = LiquidacionKPIs(
            total_general=Decimal("50000.00"),
            total_sin_factura=Decimal("50000.00"),
            total_nexo=Decimal("0"),
            total_facturantes=0,
            total_docentes=1,
        )
        resp = LiquidacionListResponse(liquidaciones=[liq], kpis=kpis)
        assert len(resp.liquidaciones) == 1

    def test_calcular_liquidacion_request_periodo_valid(self):
        s = CalcularLiquidacionRequest(
            cohorte_id=uuid.uuid4(),
            periodo="2025-06",
        )
        assert s.periodo == "2025-06"

    def test_calcular_liquidacion_request_periodo_invalid(self):
        with pytest.raises(ValidationError):
            CalcularLiquidacionRequest(
                cohorte_id=uuid.uuid4(),
                periodo="2025-13",
            )

    def test_calcular_liquidacion_request_periodo_bad_format(self):
        with pytest.raises(ValidationError):
            CalcularLiquidacionRequest(
                cohorte_id=uuid.uuid4(),
                periodo="25-06",
            )

    def test_cerrar_liquidacion_request_periodo_valid(self):
        s = CerrarLiquidacionRequest(
            cohorte_id=uuid.uuid4(),
            periodo="2025-06",
        )
        assert s.periodo == "2025-06"


class TestFacturaSchemas:
    def test_factura_create_valid(self):
        s = FacturaCreate(
            usuario_id=uuid.uuid4(),
            periodo="2025-06",
            detalle="Factura de prueba",
            referencia_archivo="ruta/factura.pdf",
            tamano_kb=Decimal("150.5"),
        )
        assert s.detalle == "Factura de prueba"

    def test_factura_create_periodo_invalid(self):
        with pytest.raises(ValidationError):
            FacturaCreate(
                usuario_id=uuid.uuid4(),
                periodo="2025-00",
                detalle="Factura invalida",
            )

    def test_factura_create_detalle_empty(self):
        with pytest.raises(ValidationError):
            FacturaCreate(
                usuario_id=uuid.uuid4(),
                periodo="2025-06",
                detalle="",
            )

    def test_factura_response_from_attributes(self):
        data = {
            "id": uuid.uuid4(),
            "usuario_id": uuid.uuid4(),
            "cohorte_id": None,
            "periodo": "2025-06",
            "detalle": "Factura test",
            "referencia_archivo": None,
            "tamano_kb": None,
            "estado": "Pendiente",
            "cargada_at": datetime.now(timezone.utc),
            "abonada_at": None,
        }
        s = FacturaResponse.model_validate(data)
        assert s.estado == "Pendiente"

    def test_factura_update_partial(self):
        s = FacturaUpdate(detalle="Correccion")
        assert s.detalle == "Correccion"
        assert s.estado is None
