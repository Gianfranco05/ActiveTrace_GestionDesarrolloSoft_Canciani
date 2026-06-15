from dataclasses import dataclass, field

from app.services.file_parser import FileParser, ParseResult

IDENTIFYING_COLUMNS = {
    "nombre", "name", "nombres", "alumno",
    "apellido", "apellidos", "surname",
    "email", "e-mail", "correo", "mail",
    "comision", "comisión", "com", "section",
    "regional", "sede", "delegacion",
}


@dataclass
class DetectedActivity:
    header: str
    nombre: str
    tipo: str


@dataclass
class GradeParseResult:
    total_rows: int
    rows: list[dict]
    activities: list[DetectedActivity] = field(default_factory=list)


def _normalize_header(header: str) -> str:
    return header.strip().lower() if header else ""


def _is_identifying(header: str) -> bool:
    return _normalize_header(header) in IDENTIFYING_COLUMNS


def _detect_tipo(header: str) -> str:
    h = header.strip()
    if h.lower().endswith("(real)"):
        return "Numerica"
    return "Textual"


def _clean_activity_name(header: str) -> str:
    h = header.strip()
    if h.lower().endswith("(real)"):
        idx = h.rfind("(", 0, len(h) - 5)
        if idx == -1:
            idx = h.lower().rindex("(real)")
        return h[:idx].strip()
    return h


class GradeFileParser(FileParser):
    def parse_grade_file(self, content: bytes, filename: str | None = None) -> GradeParseResult:
        raw: ParseResult = self.parse_bytes(content, filename)

        if not raw.rows:
            return GradeParseResult(total_rows=0, rows=[], activities=[])

        headers = list(raw.rows[0].keys()) if raw.rows else []

        activities: list[DetectedActivity] = []
        for h in headers:
            if _is_identifying(h):
                continue
            activities.append(DetectedActivity(
                header=h,
                nombre=_clean_activity_name(h),
                tipo=_detect_tipo(h),
            ))

        return GradeParseResult(
            total_rows=len(raw.rows),
            rows=raw.rows,
            activities=activities,
        )

    def get_activity_headers(self, headers: list[str]) -> list[str]:
        return [h for h in headers if not _is_identifying(h)]

    def classify_columns(self, headers: list[str]) -> dict[str, str]:
        return {h: _detect_tipo(h) for h in self.get_activity_headers(headers)}
