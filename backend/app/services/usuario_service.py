from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.auth_repository import AuthRepository
from app.core.security import encrypt_or_none, decrypt_or_none, hash_password
import uuid
from typing import Any


class UsuarioService:
    def __init__(self, repo_or_session: Any, tenant_or_db: Any):
        # Support two constructor signatures used in codebase:
        #   UsuarioService(session, tenant_id)
        #   UsuarioService(repo, db_session)
        if hasattr(repo_or_session, "create") and hasattr(repo_or_session, "get"):
            # first arg is a repository instance
            self._repo = repo_or_session
            self._db = tenant_or_db
            # try to obtain tenant_id from repo when available (repo stores _tenant_id)
            self._tenant_id = getattr(self._repo, '_tenant_id', None)
        else:
            # assume (session, tenant_id)
            session = repo_or_session
            tenant_id = tenant_or_db
            self._repo = UsuarioRepository(session, tenant_id)
            self._db = session
            self._tenant_id = tenant_id

    async def create(self, data: Any):
        # accept Pydantic model or dict
        if hasattr(data, "model_dump"):
            data = data.model_dump(exclude_none=True)
        # encrypt PII fields before passing to repo
        for f in ("dni", "cuil", "cbu", "alias_cbu"):
            if f in data:
                data[f] = encrypt_or_none(data[f])
        # Ensure an AuthUser exists and link Usuario.id to AuthUser.id
        auth_user_id = data.pop("auth_user_id", None)
        if auth_user_id is None:
            # create minimal auth user via AuthRepository
            # ensure tenant_id available for auth creation: prefer explicit, then repo
            self._tenant_id = self._tenant_id or data.get("tenant_id") or getattr(self._repo, '_tenant_id', None)
            auth_repo = AuthRepository(self._db, self._tenant_id)
            password = data.pop("password", None)
            auth_payload = {
                "email": data.pop("email", f"no-reply+{self._db}@local"),
                "password_hash": hash_password(password) if password else "",
            }
            auth = await auth_repo.create(auth_payload)
            auth_user_id = auth.id
        else:
            auth_repo = AuthRepository(self._db, self._tenant_id)
            auth = await auth_repo.get(auth_user_id)
            if auth is None:
                raise ValueError("auth_user_id does not exist")

        # attach id to usuario payload to satisfy FK PK
        data["id"] = auth_user_id
        return await self._repo.create(data)

    async def get_with_pii(self, id: uuid.UUID):
        ent = await self._repo.get(id)
        if ent is None:
            return None
        # return a plain dict with decrypted PII
        return {
            "id": str(ent.id),
            "tenant_id": str(ent.tenant_id),
            "nombre": ent.nombre,
            "apellidos": ent.apellidos,
            "dni": decrypt_or_none(ent.__dict__.get("dni")),
            "cuil": decrypt_or_none(ent.__dict__.get("cuil")),
            "cbu": decrypt_or_none(ent.__dict__.get("cbu")),
            "alias_cbu": decrypt_or_none(ent.__dict__.get("alias_cbu")),
            "banco": getattr(ent, "banco", None),
            "regional": getattr(ent, "regional", None),
            "legajo": getattr(ent, "legajo", None),
            "legajo_profesional": getattr(ent, "legajo_profesional", None),
            "facturador": ent.facturador,
            "estado": ent.estado,
            "created_at": ent.created_at,
            "updated_at": ent.updated_at,
        }

    async def list(self, **filters):
        return await self._repo.list(**filters)

    async def update(self, id: uuid.UUID, data: Any):
        if hasattr(data, "model_dump"):
            data = data.model_dump(exclude_none=True)
        # encrypt PII fields if present
        for f in ("dni", "cuil", "cbu", "alias_cbu"):
            if f in data:
                data[f] = encrypt_or_none(data[f])
        return await self._repo.update(id, data)

    async def soft_delete(self, id: uuid.UUID) -> bool:
        return await self._repo.soft_delete(id)
