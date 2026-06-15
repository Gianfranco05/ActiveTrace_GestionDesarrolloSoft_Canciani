"""TDD: Grade file parser tests."""

import io

from openpyxl import Workbook

from app.services.grade_file_parser import GradeFileParser, DetectedActivity


def _make_xlsx(headers: list[str], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_csv(headers: list[str], rows: list[list]) -> bytes:
    import csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


# ===== Group 6: Grade File Parser =====


def test_parse_detects_numeric_and_textual():
    """RED 6.1: Detects numeric and textual activities."""
    headers = ["nombre", "apellidos", "email", "TP1 (Real)", "TP2 (Real)", "Participacion", "Entrega Final"]
    rows = [["Ana", "Lopez", "ana@test.com", 75, 80, "Satisfactorio", "Aprobado"]]
    content = _make_xlsx(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content, "test.xlsx")

    activities = {a.nombre: a.tipo for a in result.activities}
    assert activities["TP1"] == "Numerica"
    assert activities["TP2"] == "Numerica"
    assert activities["Participacion"] == "Textual"
    assert activities["Entrega Final"] == "Textual"
    assert result.total_rows == 1


def test_parse_returns_total_row_count():
    """TRIANGULATE 6.4: Returns correct total row count."""
    headers = ["nombre", "apellidos", "email", "TP1 (Real)"]
    rows = [[f"Alumno{i}", f"Apellido{i}", f"e{i}@t.com", 50 + i] for i in range(48)]
    content = _make_xlsx(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content)
    assert result.total_rows == 48


def test_parse_no_numeric_activities():
    """TRIANGULATE 6.4: All textual when no (Real) columns."""
    headers = ["nombre", "apellidos", "Participacion", "TP Escrito"]
    rows = [["Ana", "Lopez", "Satisfactorio", "Aprobado"]]
    content = _make_xlsx(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content)

    for a in result.activities:
        assert a.tipo == "Textual"


def test_parse_only_identifying_columns():
    """TRIANGULATE 6.4: Only identifying columns → empty activities."""
    headers = ["nombre", "apellidos", "email"]
    rows = []
    content = _make_xlsx(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content)
    assert result.activities == []
    assert result.total_rows == 0


def test_parse_csv_format():
    """TRIANGULATE 6.4: CSV format works too."""
    headers = ["nombre", "apellidos", "TP1 (Real)", "Participacion"]
    rows = [["Ana", "Lopez", "75", "Satisfactorio"]]
    content = _make_csv(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content, "test.csv")

    activities = {a.nombre: a.tipo for a in result.activities}
    assert activities["TP1"] == "Numerica"
    assert activities["Participacion"] == "Textual"
    assert result.total_rows == 1


def test_column_normalization_case_insensitive():
    """TRIANGULATE 6.4: Case-insensitive (real) detection."""
    headers = ["nombre", "apellidos", "TP FINAL (REAL)", "tp1 (Real)", "Participacion"]
    rows = [["Ana", "Lopez", 80, 70, "Bien"]]
    content = _make_xlsx(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content)

    activities = {a.nombre: a.tipo for a in result.activities}
    assert activities["TP FINAL"] == "Numerica"
    assert activities["tp1"] == "Numerica"
    assert activities["Participacion"] == "Textual"


def test_parse_alternate_headers():
    """TRIANGULATE 6.4: Alternate identifying column names."""
    headers = ["name", "surname", "mail", "comision", "TP1 (Real)"]
    rows = [["Ana", "Lopez", "ana@t.com", "A", 80]]
    content = _make_xlsx(headers, rows)

    parser = GradeFileParser()
    result = parser.parse_grade_file(content)

    assert len(result.activities) == 1
    assert result.activities[0].nombre == "TP1"
    assert result.activities[0].tipo == "Numerica"


def test_parse_unsupported_format_raises():
    """TRIANGULATE 6.4: Unsupported format raises exception."""
    parser = GradeFileParser()
    try:
        parser.parse_grade_file(b"not a valid file at all", "test.txt")
        assert False, "Should have raised"
    except Exception:
        pass


def test_parse_empty_file():
    """TRIANGULATE 6.4: Empty file returns zero rows."""
    headers = ["nombre", "apellidos"]
    content = _make_xlsx(headers, [])

    parser = GradeFileParser()
    result = parser.parse_grade_file(content)
    assert result.total_rows == 0
    assert result.activities == []
