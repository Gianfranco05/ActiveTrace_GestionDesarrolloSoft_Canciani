from app.schemas.padron import ImportPreviewResponse


def test_import_preview_schema():
    data = {"total_rows": 2, "rows": [{"nombre": "A"}, {"nombre": "B"}]}
    resp = ImportPreviewResponse(**data)
    assert resp.total_rows == 2
