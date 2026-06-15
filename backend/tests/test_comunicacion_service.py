"""TDD: ComunicacionService tests — state machine, preview, enqueue, approve, cancel."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.services.comunicacion_service import (
    ALLOWED_TRANSITIONS,
    ComunicacionService,
    InvalidStateTransitionError,
)
from app.services.template_engine import TemplateVariables, render_template


async def _create_user(db_session, tenant):
    au = AuthUser(tenant_id=tenant.id, email="svc@test.com", password_hash="hash")
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Svc", apellidos="Test")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _create_materia(db_session, tenant):
    m = Materia(codigo="SVC-MAT", nombre="Svc Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_padron_entries(db_session, tenant, count=5):
    vp = VersionPadron(tenant_id=tenant.id, activa=True)
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)
    entries = []
    for i in range(count):
        ep = EntradaPadron(
            tenant_id=tenant.id, version_id=vp.id,
            nombre=f"Nombre{i}", apellidos=f"Apellido{i}",
            email=f"student{i}@test.com",
        )
        db_session.add(ep)
        entries.append(ep)
    await db_session.commit()
    for e in entries:
        await db_session.refresh(e)
    return entries


# ===== Group 4: State Machine =====


def test_allowed_transitions_valid():
    assert EstadoComunicacion.PENDIENTE.value in ALLOWED_TRANSITIONS
    assert EstadoComunicacion.ENVIANDO.value in ALLOWED_TRANSITIONS.get(
        EstadoComunicacion.PENDIENTE.value, [],
    )


def test_valid_transition_pendiente_to_enviando():
    ComunicacionService.validate_transition(
        EstadoComunicacion.PENDIENTE.value,
        EstadoComunicacion.ENVIANDO.value,
    )


def test_valid_transition_pendiente_to_cancelado():
    ComunicacionService.validate_transition(
        EstadoComunicacion.PENDIENTE.value,
        EstadoComunicacion.CANCELADO.value,
    )


def test_valid_transition_enviando_to_enviado():
    ComunicacionService.validate_transition(
        EstadoComunicacion.ENVIANDO.value,
        EstadoComunicacion.ENVIADO.value,
    )


def test_valid_transition_enviando_to_error():
    ComunicacionService.validate_transition(
        EstadoComunicacion.ENVIANDO.value,
        EstadoComunicacion.ERROR.value,
    )


def test_invalid_transition_enviado_to_any():
    for target in EstadoComunicacion:
        if target.value != EstadoComunicacion.ENVIADO.value:
            with pytest.raises(InvalidStateTransitionError):
                ComunicacionService.validate_transition(
                    EstadoComunicacion.ENVIADO.value, target.value,
                )


def test_invalid_transition_error_to_any():
    for target in EstadoComunicacion:
        if target.value != EstadoComunicacion.ERROR.value:
            with pytest.raises(InvalidStateTransitionError):
                ComunicacionService.validate_transition(
                    EstadoComunicacion.ERROR.value, target.value,
                )


def test_invalid_transition_cancelado_to_any():
    for target in EstadoComunicacion:
        if target.value != EstadoComunicacion.CANCELADO.value:
            with pytest.raises(InvalidStateTransitionError):
                ComunicacionService.validate_transition(
                    EstadoComunicacion.CANCELADO.value, target.value,
                )


def test_invalid_transition_enviando_to_cancelado():
    with pytest.raises(InvalidStateTransitionError):
        ComunicacionService.validate_transition(
            EstadoComunicacion.ENVIANDO.value,
            EstadoComunicacion.CANCELADO.value,
        )


def test_terminal_state_immutability():
    for terminal in [EstadoComunicacion.ENVIADO, EstadoComunicacion.ERROR, EstadoComunicacion.CANCELADO]:
        assert ALLOWED_TRANSITIONS[terminal.value] == []


# ===== Group 5: Preview Service =====


@pytest.mark.asyncio
async def test_preview_returns_sample_recipients(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=10)
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    result = await svc.preview(
        materia_id=uuid.uuid4(),
        cohorte_id=uuid.uuid4(),
        template_body="Hola {{nombre}}",
        template_asunto="Nota",
    )
    assert len(result["sample"]) == 5
    assert result["total_estimado"] == 10
    assert len(result["preview_token"]) == 16
    assert "preview_token_timestamp" in result


@pytest.mark.asyncio
async def test_preview_renders_template_variables(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=3)
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    result = await svc.preview(
        materia_id=uuid.uuid4(),
        cohorte_id=uuid.uuid4(),
        template_body="Hola {{nombre}} {{apellidos}}",
        template_asunto="Nota para {{nombre}}",
    )
    assert "Nombre0" in result["sample"][0]["cuerpo"]
    assert "Apellido0" in result["sample"][0]["cuerpo"]
    assert "Nombre0" in result["sample"][0]["asunto"]


@pytest.mark.asyncio
async def test_preview_without_recipients_raises(db_session, tenant):
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)
    with pytest.raises(HTTPException) as exc:
        await svc.preview(
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            template_body="Hola",
            template_asunto="Nota",
        )
    assert exc.value.status_code == 400


# ===== Group 6: Enqueue Service =====


@pytest.mark.asyncio
async def test_enqueue_creates_comunicacion_records(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=3)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(
        materia_id=materia.id,
        cohorte_id=uuid.uuid4(),
        template_body="Hola {{nombre}}",
        template_asunto="Nota",
    )

    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id,
        cohorte_id=uuid.uuid4(),
        template_body="Hola {{nombre}}",
        template_asunto="Nota",
    )
    assert result["creados"] == 3
    assert len(result["lote_id"]) > 0


@pytest.mark.asyncio
async def test_enqueue_without_preview_token_400(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=1)
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    with pytest.raises(HTTPException) as exc:
        await svc.enqueue(
            preview_token="invalid",
            preview_token_timestamp=datetime.now(timezone.utc).isoformat(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            template_body="Hola",
            template_asunto="Nota",
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_enqueue_expired_preview_token_400(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=1)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(
        materia_id=materia.id,
        cohorte_id=uuid.uuid4(),
        template_body="Hola",
        template_asunto="Nota",
    )

    old_ts = datetime.now(timezone.utc) - timedelta(hours=1)
    raw = f"{tenant.id}:{materia.id}:{old_ts.isoformat()}"
    old_token = hashlib.sha256(raw.encode()).hexdigest()[:16]
    with pytest.raises(HTTPException) as exc:
        await svc.enqueue(
            preview_token=old_token,
            preview_token_timestamp=old_ts.isoformat(),
            materia_id=materia.id,
            cohorte_id=uuid.uuid4(),
            template_body="Hola",
            template_asunto="Nota",
        )
    assert exc.value.status_code == 400
    assert "expired" in str(exc.value.detail).lower()


@pytest.mark.asyncio
async def test_enqueue_different_lote_id_per_call(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=2)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    p1 = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    r1 = await svc.enqueue(
        preview_token=p1["preview_token"], preview_token_timestamp=p1["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    p2 = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    r2 = await svc.enqueue(
        preview_token=p2["preview_token"], preview_token_timestamp=p2["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )
    assert r1["lote_id"] != r2["lote_id"]


@pytest.mark.asyncio
async def test_enqueue_requires_aprobacion_denormalized(db_session, tenant):
    t = await db_session.get(Tenant, tenant.id)
    t.requiere_aprobacion_comunicaciones = True
    await db_session.commit()

    entries = await _create_padron_entries(db_session, tenant, count=2)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    repo = ComunicacionRepository(db_session, tenant.id)
    items = await repo.list_by_lote(uuid.UUID(result["lote_id"]))
    for c in items:
        assert c.requiere_aprobacion is True


# ===== Group 7: Approve Service =====


@pytest.mark.asyncio
async def test_approve_by_lote(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=3)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    apr = await svc.approve(lote_id=uuid.UUID(result["lote_id"]))
    assert apr["aprobados"] == 3


@pytest.mark.asyncio
async def test_approve_by_individual_id(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=1)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    repo = ComunicacionRepository(db_session, tenant.id)
    items = await repo.list_by_lote(uuid.UUID(result["lote_id"]))
    first_id = items[0].id

    apr = await svc.approve(comunicacion_id=first_id)
    assert apr["aprobados"] == 1


@pytest.mark.asyncio
async def test_approve_already_approved_skipped(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=1)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    await svc.approve(lote_id=uuid.UUID(result["lote_id"]))
    apr2 = await svc.approve(lote_id=uuid.UUID(result["lote_id"]))
    assert apr2["aprobados"] == 0


@pytest.mark.asyncio
async def test_approve_non_existent_lote_404(db_session, tenant):
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    with pytest.raises(HTTPException) as exc:
        await svc.approve(lote_id=uuid.uuid4())
    assert exc.value.status_code == 404


# ===== Group 8: Cancel Service =====


@pytest.mark.asyncio
async def test_cancel_by_lote(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=2)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    can = await svc.cancel(lote_id=uuid.UUID(result["lote_id"]))
    assert can["cancelados"] == 2


@pytest.mark.asyncio
async def test_cancel_by_individual_id(db_session, tenant):
    entries = await _create_padron_entries(db_session, tenant, count=1)
    user = await _create_user(db_session, tenant)
    materia = await _create_materia(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)

    preview = await svc.preview(materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S")
    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id, cohorte_id=uuid.uuid4(), template_body="Hola", template_asunto="S",
    )

    repo = ComunicacionRepository(db_session, tenant.id)
    items = await repo.list_by_lote(uuid.UUID(result["lote_id"]))
    can = await svc.cancel(comunicacion_id=items[0].id)
    assert can["cancelados"] == 1


@pytest.mark.asyncio
async def test_cancel_non_existent_lote_404(db_session, tenant):
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)
    with pytest.raises(HTTPException) as exc:
        await svc.cancel(lote_id=uuid.uuid4())
    assert exc.value.status_code == 404


# ===== Group 10: Template Engine integration =====


def test_template_render_substitutes_variables():
    result = render_template(
        "Hola {{nombre}} {{apellidos}}",
        TemplateVariables(nombre="Ana", apellidos="Lopez"),
    )
    assert result == "Hola Ana Lopez"


def test_render_all_defined_variables_integration():
    t = "{{nombre}} {{apellidos}} {{email}} {{materia}} {{comision}} {{cohorte}}"
    v = TemplateVariables(
        nombre="J", apellidos="P", email="j@t.com",
        materia="M", comision="A", cohorte="2026",
    )
    assert render_template(t, v) == "J P j@t.com M A 2026"
