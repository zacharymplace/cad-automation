#!/usr/bin/env bash
set -euo pipefail

product_root="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

core_root="${ZCAD_CORE_ROOT:-$product_root/../zcad-core}"

run_repository_checks() {
  repository_name="$1"
  repository_root="$2"

  printf '\n=== %s ===\n' "$repository_name"

  if [[ ! -x "$repository_root/.venv/bin/python" ]]; then
    printf 'Virtual environment missing: %s/.venv\n' \
      "$repository_root" >&2
    exit 1
  fi

  "$repository_root/.venv/bin/ruff" \
    format --check \
    "$repository_root/src" \
    "$repository_root/tests"

  "$repository_root/.venv/bin/ruff" \
    check \
    "$repository_root/src" \
    "$repository_root/tests"

  (
    cd "$repository_root"
    .venv/bin/python -m pytest -q
  )
}

run_repository_checks \
  "zcad-core" \
  "$core_root"

run_repository_checks \
  "cad-automation" \
  "$product_root"

printf '\n=== PACKAGE BOUNDARY ===\n'

"$product_root/.venv/bin/python" - <<'PY'
from importlib.metadata import distribution

import zcad
import zcad_core

product = distribution("zcad")
core = distribution("zcad-core")

print("zcad:", product.version, zcad.__file__)
print("zcad-core:", core.version, zcad_core.__file__)

requirements = set(product.requires or [])

# A file:// reference cannot carry a version range (PEP 508), so the contract is the direct
# reference plus the installed core being new enough for the APIs cad-automation imports.
if not any(
    requirement.replace(" ", "").startswith("zcad-core@file:")
    for requirement in requirements
):
    raise SystemExit(
        "cad-automation does not declare zcad-core as a local file:// dependency"
    )

version = tuple(int(part) for part in core.version.split(".")[:2])
if version < (0, 10):
    raise SystemExit(
        f"zcad-core {core.version} is too old; cad-automation needs 0.10.0 or later "
        "(zcad_core.validation.design_report)"
    )

print("Compatibility contract: PASS")
PY

printf '\nLocal CI: PASS\n'
