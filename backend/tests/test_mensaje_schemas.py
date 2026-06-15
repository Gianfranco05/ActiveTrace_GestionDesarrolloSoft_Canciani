import uuid

import pytest
from pydantic import ValidationError

from app.schemas.mensajes import (
    MensajeCreateRequest,
    MensajeReplyRequest,
    MensajeResponse,
    InboxThreadResponse,
    ThreadDetailResponse,
)


def test_mensaje_create_rejects_missing_recipient():
    with pytest.raises(ValidationError):
        MensajeCreateRequest(asunto="Test", cuerpo="Body")


def test_mensaje_create_rejects_empty_cuerpo():
    with pytest.raises(ValidationError):
        MensajeCreateRequest(
            recipient_id=uuid.uuid4(),
            asunto="Test",
            cuerpo="",
        )


def test_mensaje_cuerpo_max_length():
    req = MensajeCreateRequest(
        recipient_id=uuid.uuid4(),
        asunto="Test",
        cuerpo="a" * 5000,
    )
    assert len(req.cuerpo) == 5000

    with pytest.raises(ValidationError):
        MensajeCreateRequest(
            recipient_id=uuid.uuid4(),
            asunto="Test",
            cuerpo="a" * 5001,
        )


def test_mensaje_asunto_max_length():
    req = MensajeCreateRequest(
        recipient_id=uuid.uuid4(),
        asunto="a" * 250,
        cuerpo="Body",
    )
    assert len(req.asunto) == 250

    with pytest.raises(ValidationError):
        MensajeCreateRequest(
            recipient_id=uuid.uuid4(),
            asunto="a" * 251,
            cuerpo="Body",
        )


def test_mensaje_reply_requires_cuerpo():
    with pytest.raises(ValidationError):
        MensajeReplyRequest()


def test_mensaje_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        MensajeCreateRequest(
            recipient_id=uuid.uuid4(),
            asunto="Test",
            cuerpo="Body",
            extra_field="value",
        )


def test_mensaje_response_from_attributes():
    msg = MensajeResponse(
        id=uuid.uuid4(),
        sender_id=uuid.uuid4(),
        sender_nombre="Emisor Test",
        recipient_id=uuid.uuid4(),
        recipient_nombre="Receptor Test",
        parent_id=None,
        asunto="Test",
        cuerpo="Body",
        leido=False,
        leido_at=None,
        created_at="2025-01-01T00:00:00Z",
    )
    assert msg.sender_nombre == "Emisor Test"
    assert msg.leido is False


def test_inbox_thread_response():
    thread = InboxThreadResponse(
        thread_id=uuid.uuid4(),
        asunto="Test thread",
        sender_nombre="Sender",
        last_message_preview="Preview...",
        message_count=5,
        unread_count=2,
        last_activity="2025-01-01T00:00:00Z",
    )
    assert thread.message_count == 5
    assert thread.unread_count == 2


def test_thread_detail_response():
    root = MensajeResponse(
        id=uuid.uuid4(),
        sender_id=uuid.uuid4(),
        sender_nombre="Root Sender",
        recipient_id=uuid.uuid4(),
        recipient_nombre="Root Recipient",
        parent_id=None,
        asunto="Root",
        cuerpo="Root body",
        leido=True,
        leido_at="2025-01-01T00:00:00Z",
        created_at="2025-01-01T00:00:00Z",
    )
    reply = MensajeResponse(
        id=uuid.uuid4(),
        sender_id=uuid.uuid4(),
        sender_nombre="Reply Sender",
        recipient_id=uuid.uuid4(),
        recipient_nombre="Reply Recipient",
        parent_id=root.id,
        asunto="Re: Root",
        cuerpo="Reply body",
        leido=False,
        leido_at=None,
        created_at="2025-01-01T00:01:00Z",
    )
    detail = ThreadDetailResponse(thread=root, replies=[reply])
    assert detail.thread.id == root.id
    assert len(detail.replies) == 1
    assert detail.replies[0].parent_id == root.id
