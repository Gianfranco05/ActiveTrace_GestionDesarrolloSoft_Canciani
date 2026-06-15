from app.services.file_parser import FileParser
from openpyxl import Workbook
import io


def test_parse_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.append(["nombre", "apellidos"])
    ws.append(["Juan", "Perez"])
    buf = io.BytesIO()
    wb.save(buf)
    content = buf.getvalue()
    parser = FileParser()
    res = parser.parse_bytes(content)
    assert res.total_rows == 1
    assert res.rows[0]["nombre"] == "Juan"
