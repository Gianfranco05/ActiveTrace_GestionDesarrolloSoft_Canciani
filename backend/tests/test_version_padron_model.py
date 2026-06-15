from app.models.padron import VersionPadron



async def test_create_version_padron(db_session, tenant):
    vp = VersionPadron(
        tenant_id=tenant.id,
        materia_id=None,
        cohorte_id=None,
        cargado_por=None,
    )
    db_session.add(vp)
    await db_session.commit()
    assert vp.id is not None
    assert vp.activa is True
