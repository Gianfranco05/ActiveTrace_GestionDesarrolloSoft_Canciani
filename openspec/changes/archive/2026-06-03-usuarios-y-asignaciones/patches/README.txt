This directory contains git-apply patch bundles prepared for review.

Files:
- 0001_usuarios_models_and_repo.patch — scaffold patch for usuario/asignacion models and repositories

Notes:
- Patches are prepared but not applied. To apply locally:
  git checkout -b feature/C-08-usuarios-y-asignaciones
  git apply --index 0001_usuarios_models_and_repo.patch
  git commit -m "feat(usuarios): add Usuario and Asignacion model scaffolds"
