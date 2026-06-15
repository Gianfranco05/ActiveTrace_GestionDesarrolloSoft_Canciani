from app.services.padron_service import PadronService
from openpyxl import Workbook
import io


def make_xlsx_bytes():
    wb = Workbook()
    ws = wb.active
    ws.append(["nombre", "apellidos", "email"])
    ws.append(["Ana", "Molina", "ana@example.com"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_preview_returns_parse_result():
    svc = PadronService(None, None)
    b = make_xlsx_bytes()
    res = svc.preview(b)
    assert res["total_rows"] == 1
