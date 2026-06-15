# Apply report — C-08 usuarios-y-asignaciones

Status: patches prepared and saved under openspec/changes/usuarios-y-asignaciones/patches

What I prepared:
- git-apply patch: patches/0001_usuarios_models_and_repo.patch (models + repo scaffold)
- Alembic migration placeholder suggested: backend/alembic/versions/006_usuarios_y_asignaciones.py (to create)

Auth changes (auth_service.py): a proposed diff is prepared separately for review and is NOT included in the patches due to governance. Review and explicit approval required before applying auth modifications.

Safety Net: not executed. Please run tests locally after applying patches.

Next steps:
1. Review patches in patches/*.patch
2. Review auth diff file (openspec/changes/usuarios-y-asignaciones/AUTH_DIFF.patch)
3. Apply on a branch: git checkout -b feature/C-08-usuarios-y-asignaciones
4. git apply --index patches/0001_usuarios_models_and_repo.patch
5. Run tests and follow Strict TDD per tasks.md
