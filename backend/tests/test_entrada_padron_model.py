from app.models.padron import VersionPadron


async def test_create_entrada_padron(db_session, tenant):
    vp = VersionPadron(tenant_id=tenant.id, materia_id=None, cohorte_id=None, cargado_por=None)
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)

    from app.repositories.padron_repository import PadronRepository
    repo = PadronRepository(db_session, tenant.id)
    e = await repo.create_entry(vp.id, {"nombre": "Pepe", "apellidos": "Lopez", "email": "pepe@example.com"})
    assert e.id is not None
    assert e.email == "pepe@example.com"
    assert e.nombre == "Pepe"


async def test_create_entries_bulk(db_session, tenant):
    vp = VersionPadron(tenant_id=tenant.id, materia_id=None, cohorte_id=None, cargado_por=None)
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)

    from app.repositories.padron_repository import PadronRepository
    repo = PadronRepository(db_session, tenant.id)
    entries = await repo.create_entries(vp.id, [
        {"nombre": "Ana", "apellidos": "Paz", "email": "ana@test.com"},
        {"nombre": "Luis", "apellidos": "Sol", "email": "luis@test.com"},
    ])
    assert len(entries) == 2
    assert entries[0].nombre == "Ana"
    assert entries[1].nombre == "Luis"
