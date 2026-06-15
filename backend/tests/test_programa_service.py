import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.programa_materia import ProgramaMateria
from app.repositories.programa_materia_repository import ProgramaMateriaRepository
from app.schemas.programas import ProgramaMateriaCreateRequest


async def _seed_prog_estructura(db_session: AsyncSession, tenant_id: uuid.UUID):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"PS-{suffix}", nombre="Test Carrera", tenant_id=tenant_id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"MAT-PS-{suffix}", nombre="Materia PS", tenant_id=tenant_id)
    db_session.add(m)
    co = Cohorte(
        id=uuid.uuid4(), carrera_id=c.id, nombre=f"COH-PS-{suffix}",
        anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant_id,
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(c)
    await db_session.refresh(m)
    await db_session.refresh(co)
    return c, m, co


class MockUploadFile:
    def __init__(self, filename: str, content: bytes = b"fake pdf content"):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


@pytest.mark.asyncio
async def test_upload_programa_creates_record(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("programa.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Programa Analitico 2026",
    )

    result = await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())
    assert result is not None
    assert result.titulo == "Programa Analitico 2026"
    assert result.materia_id == materia.id
    assert result.carrera_id == carrera.id
    assert result.cohorte_id == cohorte.id
    assert result.referencia_archivo != ""
    assert result.cargado_at is not None


@pytest.mark.asyncio
async def test_upload_empty_file_422(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("empty.pdf", b"")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Test",
    )

    with pytest.raises(HTTPException) as exc:
        await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_upload_invalid_materia_404(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("prog.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=uuid.uuid4(),
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        titulo="Test",
    )

    with pytest.raises(HTTPException) as exc:
        await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_invalid_carrera_404(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("prog.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id,
        carrera_id=uuid.uuid4(),
        cohorte_id=cohorte.id,
        titulo="Test",
    )

    with pytest.raises(HTTPException) as exc:
        await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_invalid_cohorte_404(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("prog.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=uuid.uuid4(),
        titulo="Test",
    )

    with pytest.raises(HTTPException) as exc:
        await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_filters(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("p1.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id, carrera_id=carrera.id,
        cohorte_id=cohorte.id, titulo="Prog 1",
    )
    await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())

    archivo2 = MockUploadFile("p2.pdf")
    req2 = ProgramaMateriaCreateRequest(
        materia_id=materia.id, carrera_id=carrera.id,
        cohorte_id=cohorte.id, titulo="Prog 2",
    )
    await svc.upload_programa(archivo2, req2, tenant.id, uuid.uuid4())

    items, total = await svc.listar(
        materia_id=materia.id, carrera_id=None, cohorte_id=None,
        offset=0, limit=10, tenant_id=tenant.id,
    )
    assert total == 2


@pytest.mark.asyncio
async def test_obtener_not_found_404(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    with pytest.raises(HTTPException) as exc:
        await svc.obtener(uuid.uuid4(), tenant.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_obtener_returns_programa(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("p.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id, carrera_id=carrera.id,
        cohorte_id=cohorte.id, titulo="Programa",
    )
    created = await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())

    found = await svc.obtener(created.id, tenant.id)
    assert found.id == created.id
    assert found.titulo == "Programa"


@pytest.mark.asyncio
async def test_soft_delete(db_session: AsyncSession, tenant):
    from app.services.programa_service import ProgramaService

    carrera, materia, cohorte = await _seed_prog_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)
    svc = ProgramaService(db_session, repo)

    archivo = MockUploadFile("p.pdf")
    req = ProgramaMateriaCreateRequest(
        materia_id=materia.id, carrera_id=carrera.id,
        cohorte_id=cohorte.id, titulo="To Delete",
    )
    created = await svc.upload_programa(archivo, req, tenant.id, uuid.uuid4())

    await svc.eliminar(created.id, tenant.id, uuid.uuid4())

    with pytest.raises(HTTPException) as exc:
        await svc.obtener(created.id, tenant.id)
    assert exc.value.status_code == 404
