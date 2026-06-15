This directory contains git-apply patch bundles prepared for review.

Files:
- 0001_padron_models_and_repo.patch  — scaffold patch for models and repository

Notes:
- Patches are prepared but not applied. To apply locally:
  git checkout -b feature/C-09-padron-ingesta-moodle
  git apply --index 0001_padron_models_and_repo.patch
  git commit -m "feat(padron): add VersionPadron and EntradaPadron model scaffolds"
